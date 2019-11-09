from django.shortcuts import render, HttpResponse, render_to_response, redirect
from django.db.models import Aggregate, CharField, Q
from django.http import JsonResponse
from app01 import models
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


class Concat(Aggregate):
    """ORM用来分组显示其他字段 相当于group_concat"""
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s)'

    def __init__(self, expression, distinct=False, **extra):
        super(Concat, self).__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra)


def is_error(func):
    def newfunc(request):
        try:
            res = func(request)
        except Exception as e:
            return HttpResponse('输入有误, 请重新输入')
        return res

    return newfunc


# Create your views here.
def sign_up(request):
    if request.method == 'GET':
        return render(request, 'sign_up.html')
    else:
        username = request.POST.get('username')
        if User.objects.filter(username=username):
            return HttpResponse('false')
        pwd = request.POST.get('pwd')
        if pwd:
            new_user = User.objects.create_user(username=username, password=pwd)
            login(request, new_user)
            return redirect('/app01/book_manage/')
        return HttpResponse('请输入正确的账号密码')


def login_view(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        if request.POST.get('valid_code').upper() == request.session['keep_str'].upper():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                path = request.GET.get('next') or '/app01/book_manage/'
                return redirect(path)
        return redirect('/app01/login/')


def logout_view(request):
    logout(request)
    return redirect('/app01/login/')


@login_required
def set_password(request):
    if request.method == 'GET':
        return render(request, 'set_password.html')
    else:
        user = request.user
        cur_pwd = request.POST.get('cur_pwd')
        if not user.check_password(cur_pwd):
            return HttpResponse('false')
        else:
            new_pwd = request.POST.get('new_pwd')
            if new_pwd:
                user.set_password(new_pwd)
                user.save()
                return redirect('/app01/book_manage/')
            return redirect('/app01/login/')


@login_required
def book_manage(request):
    book_list = models.Book.objects.values('id', 'title', 'price', 'pub_date',
                                           'publish__name').annotate(authors__name=Concat('authors__name'))
    return render(request, 'book_manage.html',
                  {'book_list': book_list})


@login_required
@is_error
def del_book(request):
    status = 1
    try:
        book_id = request.GET.get('book_id')
        models.Book.objects.filter(id=book_id).delete()
    except Exception:
        status = 0
    return JsonResponse({'status': status})


@login_required
@is_error
def add_book(request):
    if request.method == 'GET':
        author_list = models.Author.objects.all()
        publish_list = models.Publish.objects.all()
        return render(request, 'add_book.html', {'author_list': author_list, 'publish_list': publish_list})
    else:
        print(request.POST.dict())
        book_dict = request.POST.dict()
        book_dict.pop('csrfmiddlewaretoken')
        book_dict.pop('author')
        book = models.Book.objects.create(**book_dict)
        book.authors.add(*request.POST.getlist('author'))
        return redirect('/app01/book_manage/')


@login_required
@is_error
def edit_book(request):
    if request.method == 'GET':
        book_obj = models.Book.objects.filter(id=request.GET.get("book_id")).first()
        author_list = models.Author.objects.all()
        publish_list = models.Publish.objects.all()
        return render(request, 'edit_book.html',
                      {'author_list': author_list, 'publish_list': publish_list, 'book_obj': book_obj})
    else:
        book_obj = models.Book.objects.filter(id=request.GET.get("book_id"))
        book_dict = request.POST.dict()
        print(book_dict)
        book_dict.pop('csrfmiddlewaretoken')
        book_dict.pop('author')
        book_obj.update(**book_dict)
        book_obj.first().authors.set(request.POST.getlist('author'))
        return redirect('/app01/book_manage/')


@login_required
def author_manage(request):
    author_list = models.Author.objects.all()
    return render(request, 'author_manage.html',
                  {'author_list': author_list})


@login_required
@is_error
def add_author(request):
    if request.method == 'GET':
        audt_obj = models.AuthorDetail.objects.all().first()
        return render(request, 'add_author.html',
                      {'audt_obj': audt_obj})
    else:
        print(request.POST.dict())
        dict = request.POST.dict()
        dict.pop('csrfmiddlewaretoken')
        au_name = dict.pop('name')
        au_age = dict.pop('age')
        audt_obj = models.AuthorDetail.objects.create(**dict)
        models.Author.objects.create(name=au_name, age=au_age, au_detail_id=audt_obj.id)
        return redirect('/app01/author_manage/')


@login_required
@is_error
def edit_author(request):
    if request.method == 'GET':
        author_id = request.GET.get('author_id')
        author_obj = models.Author.objects.filter(id=author_id).first()
        audt_obj = models.AuthorDetail.objects.all().first()
        return render(request, 'edit_author.html', {'author_obj': author_obj, 'audt_obj': audt_obj})
    else:
        author_id = request.GET.get('author_id')
        dict = request.POST.dict()
        print(request.POST)
        dict.pop('csrfmiddlewaretoken')
        name = dict.pop("name")
        age = dict.pop("age")
        models.Author.objects.filter(id=author_id).update(name=name, age=age)
        models.AuthorDetail.objects.filter(author__id=author_id).update(**dict)
        return redirect('/app01/author_manage/')


@login_required
def del_author(request):
    status = 1
    try:
        author_id = request.GET.get('author_id')
        models.AuthorDetail.objects.filter(author__id=author_id).delete()
    except Exception:
        status = 0
    return JsonResponse({'status': status})


@login_required
def publish_manage(request):
    publish_list = models.Publish.objects.all()
    return render(request, 'publish_manage.html', {'publish_list': publish_list})


@login_required
def del_publish(request):
    status = 1
    try:
        publish_id = request.GET.get('publish_id')
        models.Publish.objects.filter(id=publish_id).delete()
    except Exception:
        status = 0
    return JsonResponse({'status': status})


@login_required
@is_error
def add_publish(request):
    if request.method == "GET":
        return render(request, 'add_publish.html')
    else:
        dict = request.POST.dict()
        dict.pop("csrfmiddlewaretoken")
        print(dict)
        models.Publish.objects.create(**dict)
        return redirect('/app01/publish_manage/')


@login_required
@is_error
def edit_publish(request):
    if request.method == "GET":
        publish_id = request.GET.get("publish_id")
        publish = models.Publish.objects.filter(id=publish_id).first()
        return render(request, 'edit_publish.html', {'publish': publish})
    else:
        publish_id = request.GET.get('publish_id')
        dict = request.POST.dict()
        dict.pop('csrfmiddlewaretoken')
        models.Publish.objects.filter(id=publish_id).update(**dict)
        return redirect('/app01/publish_manage/')


def get_random_rgb():
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def valid_img(request):
    img = Image.new("RGB", (135, 40), get_random_rgb())
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("/app01/statics/font/calibrib.ttf", 30)

    keep_str = ""
    for i in range(5):  # 获取随机数
        random_num = str(random.randint(0, 9))
        random_low_alpha = chr(random.randint(97, 122))
        random_upper_alpha = chr(random.randint(65, 90))
        random_char = random.choice([random_num, random_low_alpha, random_upper_alpha])
        draw.text((10 + i * 20, 0), random_char, get_random_rgb(), font=font)
        keep_str += random_char

    # 噪点噪线
    width = 135
    height = 40
    for i in range(10):
        x1 = random.randint(0, width)
        x2 = random.randint(0, width)
        y1 = random.randint(0, height)
        y2 = random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=get_random_rgb())

    for i in range(100):
        draw.point([random.randint(0, width), random.randint(0, height)], fill=get_random_rgb())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.arc((x, y, x + 4, y + 4), 0, 90, fill=get_random_rgb())

    request.session['keep_str'] = keep_str
    f = BytesIO()
    img.save(f, "png")
    data = f.getvalue()

    return HttpResponse(data)


def search(request):
    search = request.GET.get('search')
    keyword = request.POST.get('keyword')
    print(search)
    if search == '0':
        book_list = models.Book.objects.filter(
            Q(title__contains=keyword) | Q(publish__name__contains=keyword) | Q(
                authors__name__contains=keyword)).values('id', 'title', 'price', 'pub_date',
                                                         'publish__name').annotate(
            authors__name=Concat('authors__name'))
        return render(request, 'book_manage.html', {'book_list': book_list})
    elif search == '1':
        author_list = models.Author.objects.filter(
            Q(name__contains=keyword) | Q(au_detail__addr__contains=keyword) | Q(au_detail__tel=keyword) | Q(
                au_detail__birthday__contains=keyword))
        return render(request, 'author_manage.html',
                      {'author_list': author_list})
    elif search == '2':
        publish_list = models.Publish.objects.filter(
            Q(name__contains=keyword) | Q(city__contains=keyword) | Q(email=keyword))
        return render(request, 'publish_manage.html', {'publish_list': publish_list})
