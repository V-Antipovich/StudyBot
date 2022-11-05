from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.messages.views import SuccessMessageMixin
from django.core.signing import BadSignature
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView, BaseListView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin
from django.http import FileResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from .forms import UploadGtdfilesForm, GtdUpdateForm, GtdGoodCreateUpdateForm, \
    CalendarDate, ExportComment, ChangeUserInfoForm, RegisterUserForm, PaginateForm, GtdGroupCreateUpdateForm
from .models import GtdMain, GtdGroup, GtdGood, UploadGtd, CustomsHouse, Exporter, Country, Currency, Importer, DealType,\
    Procedure, TnVed, Good, GoodsMark, GtdDocument, Document, TradeMark, Manufacturer, MeasureQualifier, DocumentType,\
    UploadGtdFile, Handbook
import os
from .utilities import parse_gtd, get_tnved_name, signer
from .models import RegUser
from customs_declarations_database.settings import MEDIA_ROOT
from customs_declarations_database.Constant import under
import xlsxwriter
import mimetypes
from datetime import datetime


# TODO: docstrings!!!
# TODO: all todo in extra staff
# Вспомогательные функции контроля доступа - проверка пользователя, является ли он суперпользователем
def superuser_check(user):
    return user.is_superuser


def groups_required(allowed_roles=[]):
    def decorator(view_func):
        def wrap(request, *args, **kwargs):
            if request.user.groups.filter(name__in=allowed_roles).exists():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponseRedirect(reverse_lazy('main:access_denied'))
        return wrap
    return decorator


# Страница уведомляющая об отсутствии нужных прав
class AccessDeniedView(TemplateView):
    template_name = 'main/no_access.html'


# Авторизация
class CDDLogin(LoginView):
    template_name = 'main/login.html'


# Выход из аккаунта
class CDDLogout(LogoutView, LoginRequiredMixin):
    template_name = 'main/logout.html'


# Редактирование данных пользователя
class ChangeUserInfoView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = RegUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'

    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super(ChangeUserInfoView, self).setup(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


# Смена пароля
class RegUserPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль успешно изменен'


# Контроллер для добавления нового пользователя
@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор']), name='dispatch')
class RegisterUserView(CreateView):
    model = RegUser
    template_name = 'main/register_user.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:register_done')


# Страница сообщения об успешной регистрации
class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'


# Активация пользователя после перехода по ссылке
def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/bad_signature.html')
    user = get_object_or_404(RegUser, username=username)
    if user.is_activated:
        template = 'main/user_is_activated.html'
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)


# Страница с данными пользователя
class Profile(LoginRequiredMixin, TemplateView):
    template_name = 'main/profile.html'

    def get_context_data(self, **kwargs):
        context = super(Profile, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        context['groups'] = self.request.user.groups
        return context


# Страница '/' - перенаправление на основную
@login_required
def index(request):
    return redirect('main:show_gtd')
    # return render(request, 'main/index.html')


@login_required
def show_gtd_list(request):
    gtd_list = GtdMain.objects.all()
    paginate_by = request.GET.get('paginate_by', 10)
    page = request.GET.get('page', 1)
    paginator = Paginator(gtd_list, paginate_by)
    try:
        gtds = paginator.page(page)
    except PageNotAnInteger:
        gtds = paginator.page(1)
    except EmptyPage:
        gtds = paginator.page(paginator.num_pages)
    user = request.user
    context = {
        'gtds': gtds,
        'paginate_by': paginate_by,
        'context': user,
        'for_customs_officer': user.groups.filter(name__in=['Администратор', 'Сотрудник таможенного отдела'])
        # 'form': PaginateForm({paginate_by})
    }
    return render(request, 'main/show_gtd.html', context)


# Представление персональной страницы ГТД
@method_decorator(login_required, name='dispatch')
class GtdDetailView(DetailView):
    model = GtdMain
    template_name = 'main/per_gtd.html'
    context_object_name = 'gtd'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gtd = GtdMain.objects.filter(pk=self.kwargs.get('pk'))[0]
        gtd.recount()
        groups = GtdGroup.objects.filter(gtd_id=self.kwargs.get('pk'))
        context['groups'] = groups
        open_goods = self.request.GET.get('group')
        context['are_goods_shown'] = open_goods
        user = self.request.user
        context['user'] = user
        context['for_customs_officer'] = user.groups.filter(name__in=['Администратор', 'Сотрудник таможенного отдела']).exists()
        context['for_accountant'] = user.groups.filter(name__in=['Администратор', 'Бухгалтер']).exists()
        if open_goods:
            context['goods'] = GtdGood.objects.filter(gtd_id=self.kwargs.get('pk'), group=open_goods)
            context['current_group'] = GtdGroup.objects.filter(pk=open_goods)[0]
            # context['user'] = self.request.user.f
        return context


# TODO: ограничение доступа для классов CUD гтд
# Представление редактирования шапки ГТД
@login_required
@groups_required(allowed_roles=['Сотрудник таможенного отдела', 'Администратор'])
def update_gtd(request, pk):
    obj = get_object_or_404(GtdMain, pk=pk)
    if request.method == 'POST':
        obj.last_edited_user = request.user
        form = GtdUpdateForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('main:per_gtd', pk=pk)

    form = GtdUpdateForm(instance=obj)
    context = {
        'form': form,
        'gtd': obj,
    }
    return render(request, 'main/update_gtd.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Сотрудник таможенного отдела', 'Администратор']), name='dispatch')
class GtdGroupCreateView(CreateView):
    """
    Класс, реализующий добавление новой группы товаров в ГТД
    """
    model = GtdGroup
    template_name = 'main/create_gtd_group.html'
    context_object_name = 'group'
    form_class = GtdGroupCreateUpdateForm
    gtd = None

    def get_gtd(self):
        if not self.gtd:
            self.gtd = get_object_or_404(GtdMain, pk=self.kwargs.get('pk'))
        return self.gtd

    # Переопределение работы метода, вызываемого при валидности формы
    def form_valid(self, form):
        """
        Функция, вызываемая если форма заполнена корректно.
        Заполняет оставшееся поле и позволяет сохранить новый объект
        """
        new_group = form.save(commit=False)
        gtd = self.get_gtd() #get_object_or_404(GtdMain, pk=self.kwargs.get('pk'))
        new_group.gtd = gtd
        return super(GtdGroupCreateView, self).form_valid(form)

    def get_success_url(self):
        """
        Получение ссылки, по которой пользователь перенаправляется
        после успешного заполнения формы
        """
        return reverse('main:per_gtd', kwargs={'pk': self.kwargs.get('pk')})

    def get_context_data(self, **kwargs):
        """
        Получение контекста шаблона, добавление объекта ГТД,
        с которым добавляемая группа связана
        """
        context = super(GtdGroupCreateView, self).get_context_data(**kwargs)
        context['gtd'] = get_object_or_404(GtdMain, pk=self.kwargs.get('pk'))

        return context

    def post(self, request, *args, **kwargs):
        gtd = self.get_gtd()
        gtd.new_version()
        return super(GtdGroupCreateView, self).post(request, *args, **kwargs)


# Класс добавления нового товара в группу ГТД
@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела']), name='dispatch')
class GtdGoodCreateView(CreateView):  # TODO: last_edited
    model = GtdGood
    template_name = 'main/create_gtd_good.html'
    context_object_name = 'good'
    form_class = GtdGoodCreateUpdateForm
    group = None

    def get_group(self):
        if not self.group:
            self.group = get_object_or_404(GtdGroup, pk=self.kwargs.get('pk'))
        return self.group

    def form_valid(self, form):
        group = self.get_group()
        new_good = form.save(commit=False)
        new_good.gtd = group.gtd
        new_good.group = group
        return super(GtdGoodCreateView, self).form_valid(form)

    def get_success_url(self):
        group = self.get_group()
        return reverse('main:per_gtd', kwargs={'pk': group.gtd.pk}) + f'?group={ group.pk }'

    def get_context_data(self, **kwargs):
        context = super(GtdGoodCreateView, self).get_context_data(**kwargs)
        context['group'] = self.get_group()
        return context

    def post(self, request, *args, **kwargs):
        obj = self.get_group()
        obj.gtd.new_version()
        return super(GtdGoodCreateView, self).post(request, *args, **kwargs)


# TODO: в шаблонах для CUD сделать кнопку отмены
# Функция для редактирования группы товаров
@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела']), name='dispatch')
class GtdGroupUpdateView(UpdateView):
    model = GtdGroup
    template_name = 'main/update_gtd_group.html'
    context_object_name = 'group'
    form_class = GtdGroupCreateUpdateForm

    def get_success_url(self):
        return reverse('main:per_gtd', kwargs={'pk': self.object.gtd.pk})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.gtd.new_version()
        return super(GtdGroupUpdateView, self).post(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела']), name='dispatch')
class GtdGoodUpdateView(UpdateView):
    model = GtdGood
    template_name = 'main/update_gtd_good.html'
    context_object_name = 'good'
    form_class = GtdGoodCreateUpdateForm

    def get_success_url(self):
        return reverse('main:per_gtd', kwargs={'pk': self.object.gtd.pk}) + f'?group={ self.object.group.pk }'

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.gtd.new_version()
        return super(GtdGoodUpdateView, self).post(request, *args, **kwargs)


# Страница удаления ГТД
@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела']), name='dispatch')
class GtdDeleteView(DeleteView):
    model = GtdMain
    template_name = 'main/delete_gtd.html'
    success_url = reverse_lazy('main:show_gtd')
    context_object_name = 'gtd'


# Страница удаления группы товаров
@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела']), name='dispatch')
class GtdGroupDeleteView(DeleteView):
    model = GtdGroup
    template_name = 'main/delete_gtd_group.html'
    # success_url = reverse_lazy('main:per_gtd')
    context_object_name = 'group'

    def get_object(self, queryset=None):
        obj = super(GtdGroupDeleteView, self).get_object(queryset)
        gtd = obj.gtd
        self.success_url = reverse('main:per_gtd', kwargs={'pk': gtd.pk})
        return obj

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.gtd.new_version()
        return super(GtdGroupDeleteView, self).post(request, *args, **kwargs)


# Страница удаления товара
@method_decorator(login_required, name='dispatch')
@method_decorator(groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела']), name='dispatch')
class GtdGoodDeleteView(DeleteView):
    model = GtdGood
    template_name = 'main/delete_gtd_good.html'
    context_object_name = 'good'

    def get_object(self, queryset=None):
        obj = super(GtdGoodDeleteView, self).get_object(queryset)
        self.success_url = reverse('main:per_gtd', kwargs={'pk': obj.gtd.pk}) + f'?group={ obj.group.pk }'
        return obj

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.gtd.new_version()
        return super(GtdGoodDeleteView, self).post(request, *args, *kwargs)


# Экологический сбор: выбор периода, сбор данных о ГТД из этого периода, содержащих ТН ВЭД, подлежащие эко сбору
@login_required
@groups_required(allowed_roles=['Администратор', 'Бухгалтер'])
def eco_fee(request):
    if request.method == 'GET':
        form = CalendarDate()
        context = {
            'form': form,
            'message': ''
        }
        return render(request, 'main/ecological_fee.html', context)
    else:
        form = CalendarDate(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            start = cd['start_date']
            end = cd['end_date']
            print(type(start), type(end))

            if start <= end:
                gtds_range = GtdMain.objects.filter(date__range=[start, end])

                all_groups = GtdGroup.objects.filter(gtd_id__in=gtds_range, tn_ved__has_environmental_fee=True)

                by_tnved = {'expanded': {}, 'total': {}}
                for group in all_groups:
                    gtdId = group.gtd.gtdId
                    tn_ved = group.tn_ved.code
                    rate = group.tn_ved.collection_rate
                    standart = group.tn_ved.recycling_standart
                    weight = group.net_weight
                    row = [rate, standart, weight, rate*weight*standart/100000]

                    if tn_ved in by_tnved:
                        if gtdId in by_tnved['expanded'][tn_ved]:
                            by_tnved['expanded'][tn_ved][gtdId][2] += weight
                            by_tnved['expanded'][tn_ved][gtdId][3] += row[3]
                        else:
                            by_tnved['expanded'][tn_ved][gtdId] = row
                        by_tnved['total'][tn_ved][2] += weight
                        by_tnved['total'][tn_ved][3] += row[3]
                    else:
                        by_tnved['expanded'][tn_ved] = {}

                        by_tnved['expanded'][tn_ved][gtdId] = row
                        by_tnved['total'][tn_ved] = row

                filename = f"eco {request.user.pk} {start.strftime('%d-%m-%Y')}-{end.strftime('%d-%m-%Y')}.xlsx"
                path = os.path.join(MEDIA_ROOT, 'reports/eco', filename)
                workbook = xlsxwriter.Workbook(path)
                worksheet = workbook.add_worksheet()
                i = 1
                worksheet.write(0, 0, 'ТН ВЭД')
                worksheet.write(0, 1, 'Ставка за тонну')
                worksheet.write(0, 2, 'Норматив утилизации')
                worksheet.write(0, 3, 'Масса нетто')
                worksheet.write(0, 4, 'Сумма')
                t = by_tnved['total']
                for k in t:
                    worksheet.write(i, 0, k)
                    worksheet.write(i, 1, t[k][0])
                    worksheet.write(i, 2, t[k][1])
                    worksheet.write(i, 3, t[k][2])
                    worksheet.write(i, 4, t[k][3])
                    i += 1

                workbook.close()
                newform = CalendarDate({'start_date': start, 'end_date': end})
                context = {
                    'form': newform,
                    'show': True,
                    'start': start,
                    'end': end,
                    'filename': filename,
                    'total': by_tnved['total'],
                    'expanded': by_tnved['expanded'],
                }

                return render(request, 'main/ecological_fee.html', context)

        form = CalendarDate()
        context = {
            'form': form,
            'message': 'Некорректный диапазон. Попробуйте ещё раз.',
        }
        return render(request, 'main/ecological_fee.html', context)


# Вывод xml-файла выбранной ГТД
@login_required
def show_gtd_file(request, filename):
    get_path = os.path.join(MEDIA_ROOT, str(filename))
    return HttpResponse(open(get_path, 'r', encoding='utf-8'), content_type='application/xml')


# Представление для генерации xml-файла
@login_required
@groups_required(allowed_roles=['Администратор', 'Сотрудник таможенного отдела'])
def to_wms(request, pk):
    gtd = GtdMain.objects.filter(pk=pk)[0]
    if request.method == 'POST':
        form = ExportComment(request.POST)
        if form.is_valid():
            comment = form.cleaned_data.get('comment', '')
            gtd.export_to_wms(comment, request.user)
            return redirect('main:success', pk=pk)

    else:
        form = ExportComment()
        context = {
            'form': form,
            'gtd': gtd,
        }
        return render(request, 'main/wms.html', context)


# Формирование файла для ERP
@login_required
@groups_required(allowed_roles=['Администратор', 'Бухгалтер'])
def to_erp(request, pk):
    gtd = GtdMain.objects.filter(pk=pk)[0]
    if request.method == 'POST':
        form = ExportComment(request.POST)
        if form.is_valid():
            comment = request.POST.get('comment', '')
            gtd.export_to_erp(comment, request.user)
            return redirect('main:success', pk=pk)
            # return render(request, 'main/successful_outcome.html', context)
    else:
        form = ExportComment()
        context = {
            'form': form,
            'gtd': gtd,
        }
        return render(request, 'main/erp.html', context)


class SuccessfulOutcome(TemplateView):
    template_name = 'main/successful_outcome.html'

    def get_context_data(self, pk, **kwargs):
        context_data = super(SuccessfulOutcome, self).get_context_data(**kwargs)
        context_data['gtd'] = GtdMain.objects.filter(pk=pk)[0]
        return context_data


# Меню отчетов
class StatisticsMenu(TemplateView):
    template_name = 'main/statistic_reports_menu.html'


# Отчет - ГТД по поставщикам
@groups_required('Аналитик')
def statistics_report_gtd_per_exporter(request):
    if request.method == 'POST':
        form = CalendarDate(request.POST)
        if form.is_valid():
            start = datetime.strptime(form.data['start_date'], "%Y-%m-%d")
            end = datetime.strptime(form.data['end_date'], "%Y-%m-%d")
            gtds_range = GtdMain.objects.filter(date__range=[start, end])
            exporters = {}
            for gtd in gtds_range:
                exp = gtd.exporter.name
                if exp in exporters:
                    exporters[exp] += 1
                else:
                    exporters[exp] = 1
            exporters = list(exporters.items())
            exporters.sort(key=lambda x: x[0])
            filename = f"gtds_per_exporter {request.user.pk} {start.strftime('%d-%m-%Y')}-{end.strftime('%d-%m-%Y')}.xlsx"
            path = os.path.join(MEDIA_ROOT, 'reports/statistics', filename)
            workbook = xlsxwriter.Workbook(path)
            worksheet = workbook.add_worksheet()
            i = 1
            worksheet.write(0, 0, 'Поставщик')
            worksheet.write(0, 1, 'Количество ГТД')
            for exp in exporters:
                worksheet.write(i, 0, exp[0])
                worksheet.write(i, 1, exp[1])
                i += 1
            workbook.close()
            context = {
                'form': CalendarDate(),
                'exporters': exporters,
                'show': True,
                'filename': filename,
                'start': start,
                'end': end,
            }
            return render(request, 'main/statistics_report_gtd_per_exporter.html', context)
        else:
            form = CalendarDate()
            context = {
                'form': form,
                'message': 'Некорректный диапазон. Попробуйте ещё раз.',
            }
            return render(request, 'main/statistics_report_gtd_per_exporter.html', context)
    else:
        form = CalendarDate()
        context = {
            'form': form,
            'message': '',
        }
        return render(request, 'main/statistics_report_gtd_per_exporter.html', context)


@groups_required('Аналитик')
def statistics_report_goods_imported(request):
    if request.method == 'POST':
        form = CalendarDate(request.POST)
        if form.is_valid():
            start = datetime.strptime(form.data['start_date'], "%Y-%m-%d")
            end = datetime.strptime(form.data['end_date'], "%Y-%m-%d")

            gtds = GtdMain.objects.filter(date__range=[start, end])
            goods = GtdGood.objects.filter(gtd__in=gtds)

            unique_goods = {}
            for good in goods:
                marking = good.good.marking
                if marking in unique_goods:
                    unique_goods[marking][1] += good.quantity
                else:
                    unique_goods[marking] = [good.good.name, good.quantity]
            unique_goods = sorted(list(unique_goods.items()), key=lambda x: x[0])

            filename = f"goods_imported {request.user.pk} {start.strftime('%d-%m-%Y')}-{end.strftime('%d-%m-%Y')}.xlsx"
            path = os.path.join(MEDIA_ROOT, 'reports/statistics', filename)
            workbook = xlsxwriter.Workbook(path)
            worksheet = workbook.add_worksheet()
            i = 1
            worksheet.write(0, 0, 'Артикул')
            worksheet.write(0, 1, 'Имя товара')
            worksheet.write(0, 2, 'Количество')
            for good in unique_goods:
                worksheet.write(i, 0, good[0])
                worksheet.write(i, 1, good[1][0])
                worksheet.write(i, 2, good[1][1])
                i += 1
            workbook.close()
            context = {
                'form': CalendarDate(),
                'start': start,
                'end': end,
                'show': True,
                'goods': unique_goods,
                'filename': filename,
                # 'goods': goods,
                # 'gtds': gtds,
            }
            return render(request, 'main/statistics_report_goods_imported.html', context)
        else:
            context = {
                'form': CalendarDate(),
                'message': 'Некорректный диапазон. Попробуйте ещё раз.',
            }
            return render(request, 'main/statistics_report_goods_imported.html', context)
    else:
        form = CalendarDate()
        context = {
            'form': form,
            'message': '',
        }
        return render(request, 'main/statistics_report_goods_imported.html', context)


# Файл xlsx отчета
@groups_required('Аналитик')
def report_xlsx(request, folder, filename):
    filepath = os.path.join(MEDIA_ROOT, 'reports/', folder, filename)
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    response['Content-Disposition'] = f"attachment; filename={filename}"
    return response


@groups_required('Сотрудник таможенного отдела')
def handbook_xlsx(request, filename):
    filepath = os.path.join(MEDIA_ROOT, 'handbooks/', filename)
    path = open(filepath, 'rb')
    mime_type, _ = mimetypes.guess_type(filepath)
    response = HttpResponse(path, content_type=mime_type)
    response['Content-Disposition'] = f"attachment; filename={filename}"
    return response


# Представление обработки справочников
def handbook(request, choice):  # TODO: edit, delete
    # choice = request.GET.get('choice', 'default')

    # Словарь со всеми справочниками системы
    # Ключ - параметр url, Значение - (<Модель этого справочника>, <Название справочника для пользователей>)
    avaliable_handbooks = {
        'customs_houses': (CustomsHouse, 'Отделы таможни'),
        'exporters': (Exporter, 'Экспортеры'),  # Содержит обращение к другим моделям
        'importers': (Importer, 'Импортеры'),  # Содержит обращение к другим моделям
        'countries': (Country, 'Государства'),
        'currencies': (Currency, 'Валюты'),
        'deal_types': (DealType, 'Классификатор характера сделки'),
        'tn_ved': (TnVed, 'Классификатор ТН ВЭД'),
        'procedures': (Procedure, 'Таможенные процедуры'),
        'goods': (Good, 'Товары'),
        'trade_marks': (TradeMark, 'Товарные знаки'),  # Содержит обращение к другим моделям
        'goods_marks': (GoodsMark, 'Торговые марки'),  # Содержит обращение к другим моделям
        'manufacturers': (Manufacturer, 'Производители (заводы)'),
        'qualifiers': (MeasureQualifier, 'Единицы измерения'),
        'doc_types': (DocumentType, 'Классификатор типов документов'),
    }

    # Некоторые справочники содержат FK, которые для фронта надо подменять
    # Словарь с зависимыми моделями
    # Ключи - поля FK, которые встречаются в моделях из avaliable_handbooks
    # Значения - (<Модель, с которой через FK отношение m2o>,
    #             <Поле из этой модели, чье значение требуется>,
    #             <Порядковый номер поля в списке полей этой модели>)
    dependent_models = {
        'country_id': (Country, 'russian_name', 2),
        'goodsmark_id': (GoodsMark, 'goodsmark', 1),
        'trademark_id': (TradeMark, 'trademark', 1),
      #  'doc_type_id': (DocumentType, 'code', 1),
    }
    # По умолчанию на странице справочников будет открыт справочник товаров
    if choice == 'default':
        choice = 'goods'
    # По параметру ссылки получаем название и модель справочника
    get_handbook = avaliable_handbooks[choice]
    handbook_name = get_handbook[1]
    handbook_class = get_handbook[0]

    handbook_objects = handbook_class.objects.all()

    # Доступ к полям модели справочника
    meta = handbook_class._meta
    get_fields = meta.get_fields()

    # Массив для хранения служебной инфы для махинаций с атрибутами
    fields_system_data = []
    # Массив для имен колонок таблицы - как они будут отображаться на фронте
    fields_verbose_names = []

    for field in get_fields:
        methods = dir(field)
        # Служебное поле PK не включаем
        if '_check_primary_key' not in methods:
            # Обработаем FK - Выведем данные непосредственно из связанной таблицы
            if '_related_query_name' in methods:
                # Достаем данные связанной модели
                dependent_tuple = dependent_models[field.attname]

                dependent_model = dependent_tuple[0]
                dependent_objects = dependent_model.objects

                # Для имени колонки возьмем один объект из связанной модели
                dependent_object = dependent_models[field.attname][0].objects.last()
                needed_field = dependent_tuple[1]

                # Объекты массива служебной инфы
                # (<Bool: поле внешнего ключа?>, <Имя поля>,
                # <Объекты связанной модели>, <Нужное поле из связанной модели>)
                sys_attrs = (True, field.attname, dependent_objects, needed_field)

                # Имя поля для пользователя в связанной модели
                verbose_name = dependent_object._meta.get_fields()[dependent_tuple[2]].verbose_name

            else:
                # (<Bool: поле внешнего ключа?>, <имя поля для фронта>)
                sys_attrs = (False, field.attname)

                verbose_name = field.verbose_name

            fields_system_data.append(sys_attrs)
            fields_verbose_names.append(verbose_name)

    # Собираем непосредственно данные справочника
    handbook_data = []
    for obj in handbook_objects:
        attrs = []
        # Для каждого атрибута пройдемся по его полям
        for field in fields_system_data:
            if field[0]:
                needed_pk = getattr(obj, field[1])
                needed_raw_obj = field[2].filter(pk=needed_pk)
                if needed_raw_obj.exists():
                    needed_data = getattr(needed_raw_obj[0], field[3])
                else:
                    needed_data = ''
                # Если поле внешнего ключа, обращаемся к связанной модели и получаем данные оттуда
                # Временная заглушка
                #  needed_data = getattr(field[2].filter(pk=getattr(obj, field[1]))[0], field[3])
            else:
                # В противном случае просто обращаемся к значению нужного поля
                needed_data = getattr(obj, field[1])
                if not needed_data:
                    needed_data = ''
            attrs.append(needed_data)
        handbook_data.append(attrs)
    # print(handbook_name)

    # TODO: + фильтры, сортировка и пагинация в шаблоне
    # Если среди файлов справочников нет нужного нам, то мы должны его сейчас создать
    filename = f"{handbook_name}.xlsx"
    filepath = os.path.join(MEDIA_ROOT, 'handbooks/', filename)
    # if not os.path.exists(filepath):
    handbook_model_obj = Handbook.objects.get(name=handbook_name)
    if not os.path.exists(filepath) and not handbook_model_obj.is_actual_table:
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet()
        i, j = 1, 0
        # j = 0
        for name in fields_verbose_names:
            worksheet.write(0, j, name)
            j += 1

        for value_row in handbook_data:
            j = 0
            for value in value_row:
                worksheet.write(i, j, value)
                j += 1
            i += 1
        workbook.close()
        handbook_model_obj.is_actual_table = True
        handbook_model_obj.save()

    paginate_by = request.GET.get('paginate_by', 100)
    page = request.GET.get('page', 1)
    paginator = Paginator(handbook_data, paginate_by)
    try:
        values = paginator.page(page)
    except PageNotAnInteger:
        values = paginator.page(1)
    except EmptyPage:
        values = paginator.page(paginator.num_pages)

    context = {
        'choice': choice,
        'handbook_name': handbook_name,
        'verbose_names': fields_verbose_names,
        'values': values,
        'avaliable_handbooks': list(avaliable_handbooks.items()),
        'filename': filename,
        'paginate_by': paginate_by
        }
    return render(request, 'main/handbook.html', context)


# Загрузка файлов ГТД в формате .xml
@groups_required('Сотрудник таможенного отдела')
def upload_gtd(request):
    if request.method == 'POST':
        form = UploadGtdfilesForm(request.POST, request.FILES)
        if form.is_valid():
            on_duplicate = request.POST['on_duplicate']

            uploaded_gtd = UploadGtd(
                description=request.POST['comment']
            )
            uploaded_gtd.save()
            files = request.FILES.getlist('document')
            file_objects = []
            for file in files:
                uploaded_gtd_file = UploadGtdFile(
                    uploaded_gtd=uploaded_gtd,
                    document=file
                )
                uploaded_gtd_file.save()
                file_objects.append(uploaded_gtd_file)

            uploaded_gtd.files_num = len(file_objects)
            uploaded_gtd.save()

            all_files = len(files)
            log = {
                'skip': [],
                'new': [],
                'update': [],
            }
            for gtd in file_objects:

                last_file = gtd.document

                path = os.path.join(MEDIA_ROOT, str(last_file))
                # Получили словарь с распарсенной гтд
                get_gtdmain, get_gtdgroups = parse_gtd(path)
                # Сначала проверим, надо ли вообще добавлять ГТД, если таковая имеется.
                obj = GtdMain.objects.filter(gtdId=get_gtdmain['gtdId'])
                if obj.exists():
                    if on_duplicate == 'skip':
                        log['skip'].append(obj[0]) #get_gtdmain['gtdId'])
                        continue
                    else:
                        where_to_put = 'update'
                        # log[where_to_put].append(get_gtdmain['gtdId'])
                else:
                    where_to_put = 'new'
                    # Работа с GtdMain - основная инфа в шапке ГТД

                # Обновим справочник экспортеров если требуется
                exporter_info = get_gtdmain["exporter"]
                # add_exporter, exp_created = Exporter.objects.update_or_create(
                #     name=exporter_info["name"],
                #     postal_code=exporter_info["postal_code"],
                #     country=Country.objects.get(code=exporter_info["country"]),
                #     city=exporter_info["city"],
                #     street_house=exporter_info['street_house'],
                #     house=exporter_info["house"],
                #     region=exporter_info['region']
                # )
                add_exporter = Exporter.objects.filter(name=exporter_info["name"], postal_code=exporter_info["postal_code"])
                if add_exporter.exists():
                    add_exporter = add_exporter[0]
                else:
                    add_exporter = Exporter.objects.create(
                        name=exporter_info["name"],
                        postal_code=exporter_info["postal_code"],
                        country=Country.objects.get(code=exporter_info["country"]),
                        city=exporter_info["city"],
                        street_house=exporter_info['street_house'],
                        house=exporter_info["house"],
                        region=exporter_info['region']
                    )
                    add_exporter.save()

                # Обновим справочник импортеров
                importer_info = get_gtdmain["importer"]
                add_importer, imp_created = Importer.objects.update_or_create(
                    name=importer_info["name"],
                    inn=importer_info["inn"],
                    ogrn=importer_info["orgn"],
                )
                if imp_created:
                    add_importer.country = Country.objects.get(code=importer_info["country"])
                    add_importer.kpp = importer_info["kpp"]
                    add_importer.postal_code = importer_info["postal_code"]
                    add_importer.city = importer_info["city"]
                    add_importer.street_house = importer_info["street_house"]
                    add_importer.house = importer_info["house"]
                    add_importer.save()

                # Добавим непосредственно главную инфу гтд
                add_gtdmain, gtdmain_created = GtdMain.objects.update_or_create(
                    gtdId=get_gtdmain["gtdId"],
                    customs_house=CustomsHouse.objects.get(house_num=get_gtdmain["customs_house"]),
                    date=get_gtdmain["date"],
                    order_num=get_gtdmain["order_num"]
                )
                if gtdmain_created:
                    add_gtdmain.total_goods_number = get_gtdmain["total_goods_number"]
                    add_gtdmain.exporter = Exporter.objects.filter(name=exporter_info['name'])[0]
                    add_gtdmain.importer = Importer.objects.get(name=importer_info['name'])
                    add_gtdmain.trading_country = Country.objects.get(code=get_gtdmain["trading_country"])
                    add_gtdmain.total_cost = get_gtdmain["total_cost"]
                    add_gtdmain.currency = Currency.objects.get(short_name=get_gtdmain["currency"])
                    add_gtdmain.total_invoice_amount = get_gtdmain["total_invoice_amount"]
                    add_gtdmain.currency_rate = get_gtdmain["currency_rate"]
                    add_gtdmain.deal_type = DealType.objects.get(code=get_gtdmain["deal_type"])
                    add_gtdmain.gtd_file = gtd
                    add_gtdmain.last_edited = request.user
                    add_gtdmain.save()
                log[where_to_put].append(add_gtdmain)  # get_gtdmain['gtdId'])

                # Теперь в цикле надо пройтись по группам ГТД.
                # gtd_id = GtdMain.objects.get(gtdId=get_gtdmain["gtdId"])
                for group in get_gtdgroups:
                    # Заносим группу, если такой ещё не было
                    # Проверяем ТН ВЭД
                    code = group["tn_ved"]
                    if code[0] == '0':
                        code = code[1:]
                    tn_ved = TnVed.objects.filter(code=code)

                    # add_tnved, tnved_created = TnVed.objects.update_or_create(
                    #     code=group["tn_ved"]
                    # )
                    if len(tn_ved) == 0:
                        code = group["tn_ved"]
                        met = False
                        rec_standart = None
                        col_rate = None
                        for item in under:
                            if met:
                                break
                            for c in item:
                                if code.find(c) == 0:
                                    met = True
                                    vals = under[item]
                                    rec_standart = vals[0]
                                    col_rate = vals[1]
                                    break
                        add_tnved = TnVed.objects.create(
                            code=code,
                            subposition=get_tnved_name(code),
                            has_environmental_fee=met,
                            recycling_standart=rec_standart,
                            collection_rate=col_rate,
                        )
                        # add_tnved.subposition = get_tnved_name(str(group["tn_ved"]))
                        add_tnved.save()
                    add_gtdgroup, gtdgroup_created = GtdGroup.objects.update_or_create(
                        gtd=add_gtdmain,
                        name=group['name'],
                        # description=group['desc'],
                        tn_ved=TnVed.objects.filter(code=str(group['tn_ved']))[0],
                        number=group["number"],
                        gross_weight=group['gross_weight'],
                        net_weight=group['net_weight'],
                        country=Country.objects.get(code=group['country']),
                        procedure=Procedure.objects.get(code=group['procedure']),
                        prev_procedure=Procedure.objects.get(code=group['prev_procedure']),
                        customs_cost=group["customs_cost"],
                        fee=group["fee"],
                        ndc=group['ndc'],
                        fee_percent=group['fee_percent'],
                        ndc_percent=group['ndc_percent']
                    )

                    # Заносим в цикле товары внутри группы
                    get_goods = group["goods"]
                    for gtd_good in get_goods:
                        good_itself = gtd_good["good"]

                        # Обновляем справочник товарных знаков
                        try_trademark = good_itself['trademark']
                        if try_trademark:
                            add_trademark, trademark_created = TradeMark.objects.update_or_create(
                                trademark=try_trademark
                            )
                        else:
                            add_trademark = None

                        # Обновляем справочник торговых марок
                        try_goodsmark = good_itself['brand']
                        if try_goodsmark:
                            add_goodsmark, goodsmark_created = GoodsMark.objects.update_or_create(
                                goodsmark=try_goodsmark
                            )
                        else:
                            add_goodsmark = None

                        # Обновляем таблицу товаров
                        # add_good, good_created = Good.objects.update_or_create(
                        #     marking=good_itself['marking'],
                        #     name=good_itself['name'],
                        #     trademark=add_trademark,
                        #     goodsmark=add_goodsmark
                        # )
                        add_good = Good.objects.filter(marking=good_itself['marking'])
                        if not add_good.exists():
                            add_good = Good.objects.create(
                                marking=good_itself['marking'],
                                name=good_itself['name'],
                                trademark=add_trademark,
                                goodsmark=add_goodsmark
                            )
                        else:
                            add_good = add_good[0]

                        # Обновляем справочник производителей (заводов)
                        try_manufacturer = gtd_good['manufacturer']
                        if try_manufacturer:
                            add_manufacturer, manufacturer_created = Manufacturer.objects.update_or_create(
                                manufacturer=gtd_good['manufacturer']
                            )
                        else:
                            add_manufacturer = None

                        # Добавляем Товар ГТД
                        add_gtdgood = GtdGood.objects.filter(gtd_id=add_gtdmain.pk, group_id=add_gtdgroup.pk, good_num=gtd_good['good_num'])
                        if not add_gtdgood.exists():
                            add_gtdgood = GtdGood.objects.create(
                                gtd=add_gtdmain,
                                group=add_gtdgroup,
                                good_num=gtd_good['good_num'],
                                good=Good.objects.get(pk=add_good.pk),
                                quantity=gtd_good['quantity'],
                                qualifier=MeasureQualifier.objects.get(digital_code=gtd_good['qualifier_code']),
                                manufacturer=add_manufacturer
                            )
                            add_gtdgood.save()

                    # Заносим в цикле документы в справочник
                    gtd_documents = group['documents']

                    for gtd_document in gtd_documents:
                        add_document, document_created = Document.objects.update_or_create(
                            name=gtd_document['name'],
                            doc_type=DocumentType.objects.get(code=gtd_document['doc_type']),
                            number=gtd_document['number'],
                            date=gtd_document['date'],
                            begin_date=gtd_document['begin_date'],
                            expire_date=gtd_document['expire_date']
                        )
                        add_gtddocument, gtddocument_created = GtdDocument.objects.update_or_create(
                            gtd=add_gtdmain,
                            group=add_gtdgroup,
                            document=add_document,
                        )
            skipped = len(log['skip'])
            updated = len(log['update'])
            new = len(log['new'])
            context = {
                'log': log,
                'skipped': skipped,
                'updated': updated,
                'new': new,
                'all': skipped + updated + new,
                'test': get_goods,
            }
            return render(request, 'main/upload_gtd_log.html', context)
        # else:
        #     return render(request, 'main/error.html')

    else:
        form = UploadGtdfilesForm()
        context = {'form': form}
        return render(request, 'main/upload_gtd.html', context)

# TODO: Обработчик добавления и удаления юзеров
# TODO: Регистрация пользователей должна производиться только админом
# TODO: Контроллеры входа, сброса пароля, смены пароля
