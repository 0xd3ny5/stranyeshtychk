from pydantic import BaseModel


class SocialLink(BaseModel):
    label: str
    url: str


class SiteSettingsUpdate(BaseModel):
    artist_name: str | None = None
    artist_subtitle: str | None = None
    artist_email: str | None = None
    about_text: str | None = None
    about_photo_url: str | None = None
    contact_text: str | None = None
    contact_email: str | None = None
    social_links: list[SocialLink] | None = None


class SiteSettingsResponse(BaseModel):
    artist_name: str
    artist_subtitle: str
    artist_email: str
    about_text: str
    about_photo_url: str
    contact_text: str
    contact_email: str
    social_links: list[SocialLink]

    model_config = {"from_attributes": True}
