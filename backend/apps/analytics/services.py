from django.utils import timezone
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.db.models import Count, Sum

from apps.analytics.models import CostSimulation, GeneratedReport
from apps.audit_logs.services import log_user_action
from apps.inventory.models import Ingredient
from apps.orders.models import Order, OrderItem
from apps.tables.models import StaffPageRequest, Table
from common.utils import get_date_range, quantize_money


def build_dashboard_snapshot(start_at, end_at):
    orders = Order.objects.filter(created_at__range=(start_at, end_at))
    order_items = OrderItem.objects.filter(order__in=orders)
    revenue = orders.filter(status="paid").aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    return {
        "range": {"start_at": start_at, "end_at": end_at},
        "order_count": orders.count(),
        "paid_order_count": orders.filter(status="paid").count(),
        "revenue": quantize_money(revenue),
        "top_items": list(
            order_items.values("item_name").annotate(quantity=Sum("quantity")).order_by("-quantity", "item_name")[:5]
        ),
        "table_statuses": list(Table.objects.values("status").annotate(count=Count("id")).order_by("status")),
        "open_staff_pages": StaffPageRequest.objects.filter(status="pending").count(),
        "low_stock_ingredients": list(
            {
                "name": ingredient.name,
                "available_quantity": ingredient.available_quantity,
                "reorder_level": ingredient.reorder_level,
            }
            for ingredient in Ingredient.objects.all()
            if ingredient.available_quantity <= ingredient.reorder_level
        ),
    }


def generate_report(*, actor, range_type, start=None, end=None):
    start_at, end_at = get_date_range(range_type, start=start, end=end)
    payload = build_dashboard_snapshot(start_at, end_at)
    report = GeneratedReport.objects.create(
        generated_by=actor,
        range_type=range_type,
        start_at=start_at,
        end_at=end_at,
        payload=payload,
    )
    log_user_action(actor, "report.generated", {"report_id": report.id, "range_type": range_type}, report)
    return report


def run_cost_simulation(*, actor, menu_price_delta=Decimal("0"), monthly_salary_delta=Decimal("0"), staff_delta=0, expansion_cost=Decimal("0"), added_capacity=0):
    baseline_revenue = Order.objects.filter(status="paid").aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    baseline_orders = Order.objects.filter(status="paid").count() or 1
    projected_revenue = baseline_revenue + (baseline_orders * menu_price_delta)
    projected_cost = monthly_salary_delta + expansion_cost + Decimal(max(staff_delta, 0) * 20000)
    projected_profit = projected_revenue - projected_cost

    simulation = CostSimulation.objects.create(
        created_by=actor,
        assumptions={
            "menu_price_delta": str(menu_price_delta),
            "monthly_salary_delta": str(monthly_salary_delta),
            "staff_delta": staff_delta,
            "expansion_cost": str(expansion_cost),
            "added_capacity": added_capacity,
        },
        results={
            "baseline_revenue": str(quantize_money(baseline_revenue)),
            "projected_revenue": str(quantize_money(projected_revenue)),
            "projected_cost": str(quantize_money(projected_cost)),
            "projected_profit": str(quantize_money(projected_profit)),
            "added_capacity": added_capacity,
        },
    )
    return simulation


def backup_database(*, actor):
    backup_dir = Path(settings.BASE_DIR) / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"microblend-backup-{stamp}.sql"
    connection.ensure_connection()
    with backup_path.open("w", encoding="utf-8") as backup_file:
        for line in connection.connection.iterdump():
            backup_file.write(f"{line}\n")
    log_user_action(actor, "system.backup.created", {"path": str(backup_path)})
    return backup_path


def reset_database(*, actor):
    backup_path = backup_database(actor=actor)
    call_command("flush", "--no-input")
    return backup_path
