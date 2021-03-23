"""Functions for finding and working with Asset Browsers."""

from typing import Iterable, Optional, Tuple

import bpy
from bpy_extras import asset_utils


if "functions" not in locals():
    from . import functions
else:
    import importlib

    functions = importlib.reload(functions)


def area_for_category(
    screen: bpy.types.Screen, category: str
) -> Optional[bpy.types.Area]:
    """Return the asset browser area that is most suitable for managing the category.

    :param screen: context.window.screen
    :param category: asset category, see asset_category_items in rna_space.c

    :return: the area, or None if no Asset Browser area exists.
    """

    def area_sorting_key(area: bpy.types.Area) -> Tuple[bool, int]:
        """Return tuple (is correct category, area size in pixels)"""
        space_data = area.spaces[0]
        asset_cat: str = space_data.params.asset_category
        return (asset_cat == category, area.width * area.height)

    areas = list(suitable_areas(screen))
    if not areas:
        return None

    return max(areas, key=area_sorting_key)


def suitable_areas(screen: bpy.types.Screen) -> Iterable[bpy.types.Area]:
    """Generator, yield Asset Browser areas."""

    for area in screen.areas:
        space_data = area.spaces[0]
        if not asset_utils.SpaceAssetInfo.is_asset_browser(space_data):
            continue
        yield area


def refresh(context: bpy.types.Context) -> None:
    """Refresh all Asset Browsers."""

    # Workaround for the lack of refresh operation available to Python.
    datablock = bpy.data.objects.new("___just_refresh_me___", None)
    datablock.user_clear()  # For some reason, actions.new() already sets users=1.
    functions.asset_mark(context, datablock)
    datablock.use_fake_user = False

    # This crashes the asset browser, as it'll try to render a preview for an
    # already-deleted datablock:
    # bpy.data.objects.remove(datablock)

    # So instead of crashing, just avoid this datablock from being shown in the
    # asset browser:
    functions.asset_clear(context, datablock)


def activate_asset(
    asset: bpy.types.Action, asset_browser: bpy.types.Area, *, deferred: bool
) -> None:
    """Select & focus the asset in the browser."""

    space_data = asset_browser.spaces[0]
    assert asset_utils.SpaceAssetInfo.is_asset_browser(space_data)
    space_data.activate_asset_by_id(asset, deferred=deferred)
