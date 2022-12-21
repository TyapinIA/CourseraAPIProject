from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','slug','title']

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem

        fields = ['id','title','price','featured','category']

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id','user','menuitem','quantity','unit_price','price']
        read_only_fields =['user','price']

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['user','delivery_crew','status','total','date']
        read_only_fields =['user']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id','order','menuitem','quantity','unit_price','price']
        read_only_fields =['order','price']