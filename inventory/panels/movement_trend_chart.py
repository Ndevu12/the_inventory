"""Movement trend line chart panel."""

import json
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from wagtail.admin.ui.components import Component

from inventory.models import StockMovement


class MovementTrendChart(Component):
    """Line chart showing stock movement count per day for the last 30 days."""

    name = "movement_trend_chart"
    template_name = "inventory/panels/movement_trend_chart.html"
    order = 210

    def get_context_data(self, parent_context=None):
        context = super().get_context_data(parent_context)

        thirty_days_ago = timezone.now().date() - timedelta(days=30)

        movements_by_day = (
            StockMovement.objects.filter(created_at__date__gte=thirty_days_ago)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        counts_by_date = {entry["date"]: entry["count"] for entry in movements_by_day}

        labels = []
        data = []
        for i in range(31):
            day = thirty_days_ago + timedelta(days=i)
            labels.append(day.strftime("%Y-%m-%d"))
            data.append(counts_by_date.get(day, 0))

        context["labels_json"] = json.dumps(labels)
        context["data_json"] = json.dumps(data)
        return context
