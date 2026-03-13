from .models import Order, OrderItem


def create_order(table_session):

    order = Order.objects.create(
        table_session=table_session
    )

    return order


def add_item(order, menu_item, quantity):

    item = OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=quantity,
        price=menu_item.price
    )

    return item