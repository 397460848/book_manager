from django.urls import path, re_path
from app01 import views

urlpatterns = [
    path('sign_up/', views.sign_up),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('set_password/', views.set_password),
    path('book_manage/', views.book_manage),
    path('del_book/', views.del_book),
    path('add_book/', views.add_book),
    path('edit_book/', views.edit_book),
    path('author_manage/', views.author_manage),
    path('add_author/', views.add_author),
    path('edit_author/', views.edit_author),
    path('del_author/', views.del_author),
    path('publish_manage/', views.publish_manage),
    path('del_publish/', views.del_publish),
    path('add_publish/', views.add_publish),
    path('edit_publish/', views.edit_publish),
    path('valid_img/', views.valid_img),
    path('search/', views.search),
]
