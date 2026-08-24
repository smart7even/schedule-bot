"""empty the legacy news BDUI asset

Revision ID: b47d2f9a6e31
Revises: 8f3e2d1c4b5a
Create Date: 2026-08-24 21:00:00

The removed payload is retained in
assets/archive/news_bdui_2026-08-24.json.  The API contract remains unchanged:
GET /asset/news returns an asset whose content is an empty JSON object.
"""

from alembic import op
import sqlalchemy as sa


revision = "b47d2f9a6e31"
down_revision = "8f3e2d1c4b5a"
branch_labels = None
depends_on = None


_LEGACY_NEWS_CONTENT = {
    "card": {
        "log_id": "div2_sample_card",
        "states": [
            {
                "state_id": 0,
                "div": {
                    "type": "container",
                    "items": [
                        {
                            "type": "container",
                            "width": {"type": "match_parent"},
                            "height": {"type": "wrap_content"},
                            "items": [
                                {
                                    "type": "link",
                                    "link_text": "Официальный сайт университета",
                                    "link": "https://unecon.ru",
                                    "log": "landing",
                                    "height": {"type": "fixed", "value": 17},
                                    "margins": {"bottom": 10},
                                },
                                {
                                    "type": "link",
                                    "link_text": "Официальный сайт с расписанием",
                                    "link": "https://rasp.unecon.ru",
                                    "log": "docs",
                                    "margins": {"bottom": 10},
                                },
                                {
                                    "type": "link",
                                    "link_text": "Как добавить виджет с расписанием на домашний экран",
                                    "link": "uneconly://home_widget",
                                    "log": "tg_ru_chat",
                                    "margins": {"bottom": 10},
                                },
                            ],
                            "paddings": {"right": 10, "left": 10},
                        }
                    ],
                },
            }
        ],
    },
    "templates": {
        "tutorialCard": {
            "type": "container",
            "items": [
                {
                    "type": "text",
                    "font_size": 21,
                    "font_weight": "bold",
                    "margins": {"bottom": 16},
                    "$text": "title",
                },
                {
                    "type": "text",
                    "font_size": 16,
                    "margins": {"bottom": 16},
                    "$text": "body",
                },
                {"type": "container", "$items": "links"},
            ],
            "margins": {"bottom": 6},
            "orientation": "vertical",
            "paddings": {"top": 10, "bottom": 0, "left": 30, "right": 30},
        },
        "link": {
            "type": "text",
            "action": {"$url": "link", "$log_id": "log"},
            "font_size": 14,
            "margins": {"bottom": 2},
            "text_color": "#0000ff",
            "underline": "single",
            "$text": "link_text",
        },
    },
}


def _asset_table():
    return sa.table(
        "asset",
        sa.column("id", sa.Text()),
        sa.column("content", sa.JSON()),
    )


def upgrade():
    asset = _asset_table()
    op.execute(asset.update().where(asset.c.id == "news").values(content={}))


def downgrade():
    asset = _asset_table()
    op.execute(
        asset.update()
        .where(asset.c.id == "news")
        .values(content=_LEGACY_NEWS_CONTENT)
    )
