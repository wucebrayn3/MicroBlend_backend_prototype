from apps.orders.models import Order, OrderItem
from apps.menu.models import MenuItem

def create_order(session):
    return Order.objects.create(table_session=session)

def add_order_item(order, menu_item_id, quantity):
    menu_item = MenuItem.objects.get(id=menu_item_id)
    return OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=quantity,
        price=menu_item.price
    )

def calculate_order_total(order):
    return sum([item.price * item.quantity for item in order.items.all()])

def close_table_session(session):
    session.ended_at = session.updated_at
    session.is_active = False
    session.save()