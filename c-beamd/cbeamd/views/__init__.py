# -*- coding: utf-8 -*-
"""
Views package - split from original views.py for better organization.

This module re-exports all symbols from the split view modules to maintain
backward compatibility with existing imports and URL configurations.
"""

# Import all view functions from split modules
from .auth_views import (
    login_with_id, login, force_login, stealth_login, login_web,
    logout, stealth_logout, force_logout, logout_web,
    login_wlan, extend, tagevent, unknown_tag, welcometts
)

from .user_views import (
    getuser, getuser_eta, get_user_by_id, get_user_by_name,
    getnickspell, setnickspell, setwlanlogin, getwlanlogin,
    get_autologout, set_autologout, userlist, userlist_with_online_percentage,
    is_logged_in, ceitloch, who_result
)

from .eta_views import (
    eta, seteta, extract_eta, etalist, subeta, unsubeta,
    subarrive, unsubarrive, newetas, arrivals, achievements, activities,
    cleanup, who
)

from .event_views import (
    events, event_list, event_detail, update_event_cache, event_list_web
)

from .audio_views import (
    monmessage, tts, r2d2, play, setvolume, getvolume,
    voices, sounds, c_out, announce, c_out_web, c_out_play_web,
    remind, reminder_view
)

from .web_views import (
    index2, index, user, user_online, user_offline, user_eta, user_all,
    user_list_web, user_list, stats_list, stats, control, c_leuse,
    c_buttons, profile_edit
)

from .mission_views import (
    add_mission, missions, mission_detail, mission_assign, mission_cancel,
    mission_complete, mission_assign_web, mission_complete_web,
    mission_cancel_web, mission_list, is_mission_editor, edit_mission,
    gcm_register, gcm_update, fcm_update, gcm_send, gcm_send_mission,
    gcm_send_test
)

from .hardware_views import (
    smile, bluewall, darkwall, hwstorage, hwstorage_web,
    artefact_list, artefact_base_url_view, artefact_list_web,
    list_articles, log_stats_view, get_stats_view, list_portal_articles, app_data
)

from .stripe_views import (
    set_stripe_pattern, set_stripe_pattern_web, set_stripe_speed,
    set_stripe_speed_web, set_stripe_offset, set_stripe_buffer,
    set_stripe_default, notbeleuchtung, rainbow, stripe_view
)

from .activity_views import (
    activitylog, activitylog_web, activitylog_details_web,
    logactivity_web, logactivity, activitylog_json, not_implemented,
    activitylog_post_comment, activitylog_delete_comment
)

from .bar_views import (
    barschnur, c_portal_notify, trafotron, barstatus, get_barstatus,
    notify_bar_opening, notify_bar_closing, bar_preise, bar_leergut,
    bar_calc, bar_abrechnung, mechblast_json
)

from .preferences_views import (
    set_stats_enabled, set_push_missions, set_push_boarding, set_push_eta,
    c_out_volume_web, c_out_volume_json, c_out_volume_set,
    set_first_password, set_stealthmode, get_stealthmode,
    set_wlan_login, isWifiLoginEnabled, reminder
)

from .display_views import (
    toggle_burningman, nerdctrl, cbeamviewer, weather, bvg, welcome,
    sensors, fakelevels, dash, mechdisplay, he1display, ceitlochclocc,
    donut, reddit, barbutton, setdigitalmeter, ddate, fnord, lte,
    ampel, ampelblink, issues, hand_help, hand_commands, hand_translate,
    cerebrumNotify
)

from .mpd_views import (
    mpd_volume, mpd_status, mpd_play, mpd_stop, mpd_command,
    mpd_get_random, mpd_get_repeat, mpd_get_volume, mpd_listplaylists,
    MPDClient, ajax
)

from .health_views import (
    health_check, readiness_check, liveness_check, metrics
)

from .api_views import (
    UserViewSet, MemberViewSet, PriceViewSet, EventViewSet,
    BarViewSet, MatelightViewSet
)

from .jsonrpc_views import jsonrpc_handler

# Import shared helpers
from .view_helpers import (
    AddPadding, StripPadding, reply, logger, hysterese, eta_timeout,
    artefact_base_url, newarrivallist, newetalist, newactivities,
    achievements, eventcache, eventdetailcache, eventcache_time,
    artefactcache, artefactcache_time, cerebrum_state, hwstorage_state,
    default_stripe_pattern, default_stripe_speed, default_stripe_offset,
    mission_open, mission_assigned, mission_completed, c_out_volume,
    hand, get_prices, create_random_password, send_mail, publish, log_stats
)

# Cleanup views exported from eta_views
