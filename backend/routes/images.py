"""Image generation, library, editing, batch generation."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, HTTPException, uuid, datetime, timezone, json,
    ImageGenerateRequest, ReferenceImageData, ImageTagsRequest, ImageEditRequest,
    MultiVariantRequest, Response, Optional, List
)
from image_generator import generate_image, generate_image_variant, get_all_image_styles

router = APIRouter()

# --- Image Generation ---


@router.get("/image-styles")
async def list_image_styles():
    """Return all available image styles."""
    return get_all_image_styles()

def _sync_generate_image(job_id: str, user_id: str, prompt: str, style: str, article_id: str,
                          variation_type: str, ref_images_data: list):
    """Run image generation in a separate thread to avoid blocking event loop."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        article_context = None
        if article_id:
            article = sync_db.articles.find_one({"id": article_id}, {"_id": 0, "topic": 1, "primary_keyword": 1})
            if article:
                article_context = article

        async def _gen_with_timeout():
            if variation_type:
                coro = generate_image_variant(
                    original_prompt=prompt, style=style, variation_type=variation_type,
                    article_context=article_context, reference_images=ref_images_data
                )
            else:
                coro = generate_image(
                    prompt=prompt, style=style, article_context=article_context,
                    reference_images=ref_images_data
                )
            return await asyncio.wait_for(coro, timeout=90)

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(_gen_with_timeout())
        finally:
            loop.close()

        image_id = str(uuid.uuid4())
        image_doc = {
            "id": image_id, "user_id": user_id, "prompt": prompt, "style": style,
            "article_id": article_id, "variation_type": variation_type,
            "mime_type": result["mime_type"], "data": result["data"],
            "has_reference": ref_images_data is not None,
            "num_references": len(ref_images_data) if ref_images_data else 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        sync_db.images.insert_one(image_doc)

        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "completed", "result": {
                "id": image_id, "prompt": prompt, "style": style,
                "mime_type": result["mime_type"], "data": result["data"],
                "created_at": image_doc["created_at"]
            }, "updated_at": datetime.now(timezone.utc)}}
        )
    except Exception as e:
        logging.error(f"Image generation job {job_id} failed: {e}")
        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now(timezone.utc)}}
        )
    finally:
        sync_client.close()


@router.post("/images/generate")
async def generate_image_endpoint(request: ImageGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate an image using Gemini Nano Banana model (async with polling)."""
    try:
        allowed_mime = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        ref_images_list = []
        if request.reference_images:
            for ref in request.reference_images:
                if ref.mime_type not in allowed_mime:
                    raise HTTPException(status_code=400, detail=f"Nieobslugiwany format pliku: {ref.mime_type}. Dozwolone: PNG, JPG, WEBP")
                if len(ref.data) > 7_000_000:
                    raise HTTPException(status_code=400, detail="Jeden z plikow jest zbyt duzy. Maksymalny rozmiar: 5MB")
                ref_images_list.append({"data": ref.data, "mime_type": ref.mime_type})
        elif request.reference_image:
            if request.reference_image.mime_type not in allowed_mime:
                raise HTTPException(status_code=400, detail="Nieobslugiwany format pliku. Dozwolone: PNG, JPG, WEBP")
            if len(request.reference_image.data) > 7_000_000:
                raise HTTPException(status_code=400, detail="Plik jest zbyt duzy. Maksymalny rozmiar: 5MB")
            ref_images_list.append({"data": request.reference_image.data, "mime_type": request.reference_image.mime_type})

        ref_images_data = ref_images_list if ref_images_list else None
        job_id = str(uuid.uuid4())
        await db.image_generation_jobs.insert_one({
            "job_id": job_id, "status": "processing",
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
        })

        asyncio.get_event_loop().run_in_executor(
            None, _sync_generate_image, job_id, user["id"], request.prompt, request.style,
            request.article_id, request.variation_type, ref_images_data
        )
        return {"job_id": job_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/generate/status/{job_id}")
async def image_generation_status(job_id: str):
    """Poll image generation job status."""
    job = await db.image_generation_jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Detect stale image jobs (stuck processing > 120s)
    if job["status"] == "processing":
        created = job.get("created_at")
        if created:
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace("Z", "+00:00"))
            # Ensure both datetimes are offset-aware
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - created).total_seconds()
            if elapsed > 120:
                await db.image_generation_jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {"status": "failed", "error": "Generowanie obrazu przekroczylo limit czasu. Sprobuj ponownie."}}
                )
                await db.image_generation_jobs.delete_one({"job_id": job_id})
                return {"status": "failed", "error": "Generowanie obrazu przekroczylo limit czasu. Sprobuj ponownie."}

    if job["status"] == "completed":
        await db.image_generation_jobs.delete_one({"job_id": job_id})
        return {"status": "completed", "result": job.get("result", {})}
    if job["status"] == "failed":
        await db.image_generation_jobs.delete_one({"job_id": job_id})
        return {"status": "failed", "error": job.get("error", "Unknown error")}
    return {"status": "processing"}


@router.get("/images/{image_id}")
async def get_image(image_id: str):
    """Get a single image by ID."""
    image = await db.images.find_one({"id": image_id}, {"_id": 0})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "id": image["id"],
        "prompt": image.get("prompt", ""),
        "style": image.get("style", ""),
        "mime_type": image.get("mime_type", ""),
        "data": image.get("data", ""),
        "article_id": image.get("article_id"),
        "created_at": image.get("created_at")
    }


@router.get("/articles/{article_id}/images")
async def get_article_images(article_id: str):
    """Get all images for a specific article (with base64 data for thumbnails)."""
    images = await db.images.find(
        {"article_id": article_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return images


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an image."""
    result = await db.images.delete_one({"id": image_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image deleted", "id": image_id}


# --- Image Library ---

@router.get("/library/images")
async def library_list_images(
    q: Optional[str] = None,
    style: Optional[str] = None,
    tag: Optional[str] = None,
    article_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """List all images for current user (admin sees all). Supports filtering."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    
    if q:
        query["prompt"] = {"$regex": q, "$options": "i"}
    if style:
        query["style"] = style
    if tag:
        query["tags"] = tag
    if article_id:
        query["article_id"] = article_id
    
    # Get total count
    total = await db.images.count_documents(query)
    
    # Fetch images - include data for thumbnails
    images = await db.images.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    # Mark all as having data
    for img in images:
        img["has_data"] = bool(img.get("data"))
    
    return {
        "images": images,
        "total": total,
        "limit": limit,
        "offset": offset
    }



@router.put("/images/{image_id}/tags")
async def update_image_tags(image_id: str, request: ImageTagsRequest, user: dict = Depends(get_current_user)):
    """Update tags on an image."""
    image = await db.images.find_one({"id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not user.get("is_admin") and image.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    # Clean tags
    clean_tags = [t.strip().lower() for t in request.tags if t.strip()]
    await db.images.update_one(
        {"id": image_id},
        {"$set": {"tags": clean_tags, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"id": image_id, "tags": clean_tags}


@router.get("/library/tags")
async def library_list_tags(user: dict = Depends(get_current_user)):
    """List all unique tags for current user's images."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    pipeline = [
        {"$match": {**query, "tags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 50}
    ]
    tags = await db.images.aggregate(pipeline).to_list(50)
    return [{"tag": t["_id"], "count": t["count"]} for t in tags]


# --- AI Image Editing ---


@router.post("/images/edit")
async def edit_image_endpoint(request: ImageEditRequest, user: dict = Depends(get_current_user)):
    """AI-powered image editing: inpaint, background change, style transfer."""
    try:
        # Get source image
        source_data = None
        if request.image_id:
            img_doc = await db.images.find_one({"id": request.image_id})
            if not img_doc:
                raise HTTPException(status_code=404, detail="Obraz zrodlowy nie znaleziony")
            source_data = {"data": img_doc["data"], "mime_type": img_doc["mime_type"]}
        elif request.source_image:
            source_data = {"data": request.source_image.data, "mime_type": request.source_image.mime_type}
        
        if not source_data:
            raise HTTPException(status_code=400, detail="Wymagany obraz zrodlowy (image_id lub source_image)")
        
        # Build edit prompt based on mode
        mode_instructions = {
            "inpaint": f"Modify this image based on the following instruction: {request.prompt}. Keep the overall composition but make the requested changes. Maintain professional quality.",
            "background": f"Change the background of this image: {request.prompt}. Keep the main subject/foreground elements intact but replace the background as described.",
            "style_transfer": f"Transform the style of this image: {request.prompt}. Keep the content and composition but apply the described artistic style.",
            "enhance": f"Enhance this image: {request.prompt}. Improve quality, colors, and details while maintaining the original content."
        }
        
        edit_prompt = mode_instructions.get(request.mode, mode_instructions["enhance"])
        
        result = await generate_image(
            prompt=edit_prompt,
            style="custom",
            reference_images=[source_data]
        )
        
        # Save edited image
        image_id = str(uuid.uuid4())
        image_doc = {
            "id": image_id,
            "user_id": user["id"],
            "prompt": request.prompt,
            "style": f"edit_{request.mode}",
            "article_id": None,
            "variation_type": None,
            "edit_mode": request.mode,
            "source_image_id": request.image_id,
            "mime_type": result["mime_type"],
            "data": result["data"],
            "tags": [request.mode, "edycja"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.images.insert_one(image_doc)
        
        return {
            "id": image_id,
            "prompt": request.prompt,
            "mode": request.mode,
            "mime_type": result["mime_type"],
            "data": result["data"],
            "created_at": image_doc["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image edit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Multi-variant Generation ---

def _sync_generate_batch(job_id: str, user_id: str, prompt: str, style: str,
                          article_id: str, num_variants: int, ref_images_data: list):
    """Run batch image generation in a separate thread."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        article_context = None
        if article_id:
            article = sync_db.articles.find_one({"id": article_id}, {"_id": 0, "topic": 1, "primary_keyword": 1})
            if article:
                article_context = article

        variant_suffixes = [
            "",
            " Create a different composition with alternative layout.",
            " Use a warmer, more inviting color palette.",
            " Make it more minimalist and clean with extra white space."
        ]

        saved = []
        for i in range(num_variants):
            modified_prompt = prompt + variant_suffixes[i]
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(generate_image(
                    prompt=modified_prompt, style=style,
                    article_context=article_context, reference_images=ref_images_data
                ))
            except Exception as e:
                saved.append({"error": str(e), "variant_index": i})
                continue
            finally:
                loop.close()

            image_id = str(uuid.uuid4())
            image_doc = {
                "id": image_id, "user_id": user_id, "prompt": prompt, "style": style,
                "article_id": article_id, "variation_type": f"batch_{i}",
                "mime_type": result["mime_type"], "data": result["data"],
                "tags": ["batch"], "created_at": datetime.now(timezone.utc).isoformat()
            }
            sync_db.images.insert_one(image_doc)
            saved.append({
                "id": image_id, "prompt": prompt, "style": style, "variant_index": i,
                "mime_type": result["mime_type"], "data": result["data"],
                "created_at": image_doc["created_at"]
            })
            # Update progress
            sync_db.image_generation_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"progress": i + 1, "updated_at": datetime.now(timezone.utc)}}
            )

        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "completed", "result": {"variants": saved, "total": len(saved)}, "updated_at": datetime.now(timezone.utc)}}
        )
    except Exception as e:
        logging.error(f"Batch generation job {job_id} failed: {e}")
        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now(timezone.utc)}}
        )
    finally:
        sync_client.close()


@router.post("/images/generate-batch")
async def generate_batch_endpoint(request: MultiVariantRequest, user: dict = Depends(get_current_user)):
    """Generate multiple image variants at once (async with polling)."""
    if request.num_variants < 1 or request.num_variants > 4:
        raise HTTPException(status_code=400, detail="Liczba wariantow musi byc od 1 do 4")

    try:
        allowed_mime = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        ref_images_list = []
        if request.reference_images:
            for ref in request.reference_images:
                if ref.mime_type not in allowed_mime:
                    raise HTTPException(status_code=400, detail=f"Nieobslugiwany format pliku: {ref.mime_type}")
                ref_images_list.append({"data": ref.data, "mime_type": ref.mime_type})
        elif request.reference_image:
            if request.reference_image.mime_type not in allowed_mime:
                raise HTTPException(status_code=400, detail="Nieobslugiwany format pliku")
            ref_images_list.append({"data": request.reference_image.data, "mime_type": request.reference_image.mime_type})
        ref_images_data = ref_images_list if ref_images_list else None

        job_id = str(uuid.uuid4())
        await db.image_generation_jobs.insert_one({
            "job_id": job_id, "status": "processing", "progress": 0,
            "total": request.num_variants,
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
        })
        asyncio.get_event_loop().run_in_executor(
            None, _sync_generate_batch, job_id, user["id"], request.prompt, request.style,
            request.article_id, request.num_variants, ref_images_data
        )
        return {"job_id": job_id, "status": "processing", "total": request.num_variants}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


