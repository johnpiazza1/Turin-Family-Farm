from __future__ import annotations

from datetime import date

from .analysis import HiveState

_SEASONAL: dict[tuple[int, ...], list[str]] = {
    (3, 4): [
        "Spring buildup: monitor for swarm cells weekly",
        "Add supers early — nectar flow can start suddenly",
        "Check that queens have room to lay",
        "Consider splits if populations are booming",
    ],
    (5, 6): [
        "Peak swarm season: inspect every 7 days",
        "Watch for queen cells; make splits or remove cells proactively",
        "Add honey supers as needed",
        "Run mite counts before summer dearth",
    ],
    (7, 8): [
        "Summer dearth: reduce entrances, watch for robbing",
        "Monitor water sources",
        "Treat mites before fall brood ramp-up if counts are elevated",
        "Check honey supers — extract when frames are 80%+ capped",
    ],
    (9, 10): [
        "Fall prep: treat mites now to protect winter bees",
        "Ensure 60–80 lbs of honey stores per hive before winter",
        "Combine weak hives rather than wintering them thin",
        "Stop extracting by mid-September to leave stores",
    ],
    (11, 12): [
        "Pre-winter: entrance reducers on, mouse guards in place",
        "Do not open hives below 50°F",
        "Heft hives to check stores; feed if light",
        "Ventilate tops to prevent moisture buildup",
    ],
    (1, 2): [
        "Winter cluster: minimal disturbance",
        "On warm days (>50°F), check for cluster location and food proximity",
        "Plan spring splits and queen-rearing calendar now",
        "Order queens or grafting supplies if needed",
    ],
}


def _month_to_pair(month: int) -> tuple[int, ...]:
    for pair in _SEASONAL:
        if month in pair:
            return pair
    return (month,)


def get_seasonal_advice(states: list[HiveState], today: date | None = None) -> list[str]:
    if today is None:
        today = date.today()

    advice = list(_SEASONAL.get(_month_to_pair(today.month), []))

    overdue = [h.hive_id for h in states if h.is_overdue]
    if overdue:
        advice.append(f"Overdue inspections: {', '.join(overdue)} — schedule immediately")

    high_mite_untreated = [
        h.hive_id for h in states
        if h.mite_rate is not None
        and h.mite_rate >= 2
        and h.treatment_status.lower() not in ("complete", "in progress", "treating")
    ]
    if high_mite_untreated:
        advice.append(
            f"Mite rate ≥2% without active treatment: {', '.join(high_mite_untreated)} — treat now"
        )

    queens_past_due = []
    for h in states:
        if h.larvae_next_date and (today - h.larvae_next_date).days > 0 and h.larvae_next_critical:
            queens_past_due.append(f"{h.hive_id} ({h.larvae_next_critical})")
    if queens_past_due:
        advice.append(f"Queen rearing milestone overdue: {', '.join(queens_past_due)}")

    return advice
