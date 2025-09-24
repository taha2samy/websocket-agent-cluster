from .async_helpers import get_broker_token, get_permissions, matcher

async def check_tags_permissions(token_str, tags_str):
    """
    Check the token and tags, return a tuple:
    ({ tag1: permission1, tag2: permission2, ... }, max_connections)
    Returns None if token invalid or any tag not allowed.
    """
    # Split the tags by comma
    tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]

    # Fetch the token object
    token_obj = await get_broker_token(token_str)
    if not token_obj:
        return None  # Token not found → reject

    max_connections = token_obj.max_connections

    # Fetch all allowed prefixes and permissions for this token
    allowed_prefixes = await get_permissions(token_obj)
    # allowed_prefixes = [(prefix, permission), ...]

    tag_permissions = {}

    for tag in tags_list:
        matched = False
        for prefix, permission in allowed_prefixes:
            if matcher.is_match(tag, [prefix])["match"]:
                tag_permissions[tag] = permission
                matched = True
                break

        if not matched:
            return None

    return (tag_permissions, max_connections) if tag_permissions else None
