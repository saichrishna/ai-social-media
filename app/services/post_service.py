saved_post = (
    self.social_post_repository
    .create_post(post_data)
)

if not saved_post:
    raise ValueError(
        "Failed to save social post."
    )

post = saved_post[0]

# -----------------------------------
# GENERATE POST IMAGE
# -----------------------------------

image_result = None

image_prompt = post.get("image_prompt")

if image_prompt:

    try:

        image_result = (
            self.media_generation
            .generate_post_image(
                post_id=post["id"],
                prompt=image_prompt
            )
        )

        # -----------------------------------
        # UPDATE POST WITH IMAGE PATH
        # -----------------------------------

        updated_post = (
            self.social_post_repository
            .update_post(
                post["id"],
                {
                    "image_url": (
                        image_result["storage_path"]
                    )
                }
            )
        )

        if updated_post:
            post = updated_post[0]

    except Exception as image_error:

        # Image failure should NOT destroy
        # an otherwise valid generated post.

        image_result = {
            "success": False,
            "error": str(image_error)
        }

return {
    "success": True,
    "status": status,
    "attempt": attempt,

    "post": post,

    "brand": (
        brand_profile.model_dump()
        if brand_profile
        else None
    ),

    "prompt_engineering": prompt_result,

    "content": content,

    "review": review,

    "attempt_history": attempts,

    "image": image_result
}