from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth.models import User, Group
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes, throttle_classes
from rest_framework.response import Response
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, CategorySerializer, CartSerializer, OrderItemSerializer, OrderSerializer
from rest_framework import generics
from datetime import datetime
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

# Adds user to manager group and delivery crew
@api_view(['Get','POST','DELETE'])
@throttle_classes([UserRateThrottle])
@permission_classes([IsAdminUser])
def managers(request):
    
    if request.method == "GET":
        users = User.objects.filter(groups__name='manager').values('username')
        return Response (users)
    
    username = request.data['username']  
    if username:
        user = get_object_or_404(User, username=username)      
    
    if request.method == 'POST':
        if request.user.groups.filter(name = 'manager').exists():
            delivery_crew = Group.objects.get(name='delivery-crew')
            delivery_crew.user_set.add(user)
            user.save()
            return Response({'message':'User '+username+' added to delivery crew'},201)
        else:
            managers = Group.objects.get(name='manager')
            managers.user_set.add(user)
            user.is_staff=True
            user.save()
            return Response({'message':'User '+username+' added managers'},201)
    
    
    elif request.method == 'DELETE':
        if request.user.groups.filter(name = 'manager').exists():
            delivery_crew = Group.objects.get(name='delivery-crew')
            delivery_crew.user_set.remove(user)
            user.save()
            return Response({'message':'user '+username+' deleted from delivery crew'})
        else:
            managers = Group.objects.get(name='manager')
            managers.user_set.remove(user)
            user.is_staff=False
            user.save()
            return Response({'message':'user '+username+' deleted from managers'})
    return Response({'message':'error'},status.HTTP_400_BAD_REQUEST)


# Menu-items manipulation
class MenuItems (generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields=['price']
    search_fields=['category__title']
    def get_permissions(self):
        if(self.request.method=='GET'):
            return [IsAuthenticated()]
        return [IsAdminUser()]

# Done category manipulation
class CategoryItems(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get(self,request):
        items = Category.objects.all()
        serialized_item = CategorySerializer(items, many=True)
        return Response(serialized_item.data,200)
    def post(self,request):
        serialized_item = CategorySerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save()
        return Response(serialized_item.data,201)
    def delete (self,request):
        categorise = Category.objects.all()
        categorise.delete()
    def get_permissions(self):
        if(self.request.method=='GET'):
            return [IsAuthenticated()]
        return [IsAdminUser()]

# Done single menu-item manipulation
class MenuItemSingle(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get(self,request,pk):
        item = MenuItem.objects.get(pk=pk)
        serialized_item = MenuItemSerializer(item)
        return Response(serialized_item.data,200)   
    
    def patch(self,request,pk):
        item = MenuItem.objects.get(pk=pk)
        serialized_item = MenuItemSerializer(data=request.data)
        serialized_item.is_valid()

        if serialized_item.data['featured']:
            item.featured = serialized_item.data['featured']
            item.save()
            return Response('Item '+item.title+' featured set to '+str(item.featured),200)
        else: return Response("Incorrect input",401)
    
    def delete(self, request, pk):
        item = MenuItem.objects.get(pk=pk)
        item.delete()
        return Response ('Menu item deleted',200)
    def get_permissions(self):
        if(self.request.method=='GET'):
            return [IsAuthenticated()]
        return [IsAdminUser()]

# Done action with cart
class CartView(generics.ListCreateAPIView,generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes=[IsAuthenticated]

    def get (self,request):
        queryset = Cart.objects.all().filter(user=self.request.user)
        serializer_class = CartSerializer(queryset, many=True)
        return Response(serializer_class.data,200)
    def post(self,request):
        price = float(request.data['quantity'])*float(request.data['unit_price'])
        serialized_item = CartSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        serialized_item.save(user = self.request.user, price=price)
        return Response(serialized_item.data,201)
    def delete (self,request):
        queryset = Cart.objects.all().filter(user=self.request.user)
        queryset.delete()
        return Response('Cart deleted',200)



# Done actions with order
class OrderItemView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes=[IsAuthenticated]

    def get (self,request):
        queryset = OrderItem.objects.all().filter(order = request.user)
        serializer_class = OrderItemSerializer(queryset, many=True)
        return Response(serializer_class.data,200)
    def post(self, request):
        # checks if date was inputed
        try:
            date = request.data['date']
        except:
            return Response ('Date needed',400)
        # checks if date was inputed in corrext format
        try:
            date = datetime.strptime(request.data['date'], '%Y-%m-%d').date()   
        except:
            return Response ('Wrong date format',400)

        try:
            user=self.request.user
            items = Cart.objects.all().filter(user=user)
            total_cost = 0
            #try:
            for item in items:
                serialized_item = CartSerializer(item)
                data = serialized_item.data
                price = float(data['quantity'])*float(data['unit_price'])
                # Sends data to OrderItem
                total_cost=total_cost+price             
                serialized_item = OrderItemSerializer(data=data)
                serialized_item.is_valid()
                serialized_item.save(order = self.request.user, price=price)
            new_order = Order(
            user=user,
            delivery_crew = None,
            status = 0,
            total = total_cost,
            date = request.data['date']
            )
            new_order.save()
            items.delete()
            return Response('Order made',201)
        except:
            return Response ('Order of selected item is already made',400)


# actions with delivery table:

class DeliveryView(generics.ListAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes=[IsAuthenticated]
    def get (self,request):
        if request.user.groups.filter(name = 'delivery-crew').exists():
            queryset = Order.objects.all().filter(delivery_crew=self.request.user)
            serializer_class = OrderSerializer(queryset, many=True)
            return Response (serializer_class.data,200)

class DeliverySingleView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    permission_classes=[IsAuthenticated]
    def patch(self,request,pk):
        order = Order.objects.get(pk=pk)
        serialized_item = OrderSerializer(data=request.data)
        serialized_item.is_valid()
        if request.user.groups.filter(name = 'delivery-crew').exists():
            if serialized_item.data['status']:
                order.status = serialized_item.data['status']
                order.save()
                return Response('Order status set to '+str(request.data['status']),201)        
        elif request.user.groups.filter(name = 'manager').exists():
            if serialized_item.data['delivery_crew']:
                crew = User.objects.get(id = serialized_item.data['delivery_crew'])
                order.delivery_crew = crew
                order.save()
                return Response('Order assigned to '+str(request.data['delivery_crew']+' crew member'),201)
    def delete(self,request,pk):
        order = Order.objects.get(pk=pk)
        order.delete()
        return Response('Order deleted',200)
