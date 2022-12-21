from django.urls import path
from . import views

urlpatterns = [

	path('groups/manager/users',views.managers),
	path('categories',views.CategoryItems.as_view()),
	path('menu-items',views.MenuItems.as_view()),
	path('menu-items/<int:pk>',views.MenuItemSingle.as_view()),
	path('cart/menu-items',views.CartView.as_view()),
	path('cart/orders',views.OrderItemView.as_view()),
	path('orders', views.DeliveryView.as_view()),
	path('orders/<int:pk>', views.DeliverySingleView.as_view()),


]
