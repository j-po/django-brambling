from django.conf.urls import patterns, url, include
from django.core.urlresolvers import reverse_lazy

from brambling.forms.user import FloppyAuthenticationForm
from brambling.views.attendee import (
    ReservationView,
    CartView,
    CheckoutView,
)
from brambling.views.core import (
    UserDashboardView,
    EventListView,
)
from brambling.views.organizer import (
    EventCreateView,
    EventUpdateView,
    ItemListView,
    item_form,
    DiscountListView,
    discount_form,
)
from brambling.views.user import (
    PersonView,
    HomeView,
    SignUpView,
    EmailConfirmView,
    send_confirmation_email_view,
    CreditCardAddView,
    CreditCardDeleteView,
)
from brambling.views.utils import split_view, route_view, get_event_or_404


urlpatterns = patterns('',
    url(r'^$',
        split_view(lambda r, *a, **k: r.user.is_authenticated(),
                   UserDashboardView.as_view(),
                   EventListView.as_view()),
        name="brambling_dashboard"),
    url(r'^create/$',
        EventCreateView.as_view(),
        name="brambling_event_create"),

    url(r'^login/$',
        'django.contrib.auth.views.login',
        {'authentication_form': FloppyAuthenticationForm},
        name='login'),
    url(r'^', include('django.contrib.auth.urls')),
    url(r'^signup/$',
        SignUpView.as_view(),
        name="brambling_signup"),
    url(r'^email_confirm/send/$',
        send_confirmation_email_view,
        name="brambling_email_confirm_send"),
    url(r'^email_confirm/(?P<pkb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})$',
        EmailConfirmView.as_view(),
        name="brambling_email_confirm"),

    url(r'^profile/$',
        PersonView.as_view(),
        name="brambling_user_profile"),
    url(r'^profile/card/add/$',
        CreditCardAddView.as_view(),
        name="brambling_user_card_add"),
    url(r'^profile/card/delete/(?P<pk>\d+)/$',
        CreditCardDeleteView.as_view(),
        name="brambling_user_card_delete"),
    url(r'^home/$',
        HomeView.as_view(),
        name="brambling_home"),

    url(r'^(?P<slug>[\w-]+)/$',
        route_view(lambda r, *a, **k: get_event_or_404(k['slug']
                                                       ).editable_by(r.user),
                   'edit/',
                   'reserve/'),
        name="brambling_event_detail"),
    url(r'^(?P<slug>[\w-]+)/reserve/$',
        ReservationView.as_view(),
        name="brambling_event_reserve"),
    url(r'^(?P<slug>[\w-]+)/cart/$',
        CartView.as_view(),
        name="brambling_event_cart"),
    url(r'^(?P<slug>[\w-]+)/checkout/$',
        CheckoutView.as_view(),
        name="brambling_event_checkout"),
    url(r'^(?P<slug>[\w-]+)/edit/$',
        EventUpdateView.as_view(),
        name="brambling_event_update"),

    url(r'^(?P<event_slug>[\w-]+)/items/$',
        ItemListView.as_view(),
        name="brambling_item_list"),
    url(r'^(?P<event_slug>[\w-]+)/items/create/$',
        item_form,
        name="brambling_item_create"),
    url(r'^(?P<event_slug>[\w-]+)/items/(?P<pk>\d+)/$',
        item_form,
        name="brambling_item_update"),

    url(r'^(?P<event_slug>[\w-]+)/discount/$',
        DiscountListView.as_view(),
        name="brambling_discount_list"),
    url(r'^(?P<event_slug>[\w-]+)/discount/create/$',
        discount_form,
        name="brambling_discount_create"),
    url(r'^(?P<event_slug>[\w-]+)/discount/(?P<pk>\d+)/$',
        discount_form,
        name="brambling_discount_update"),
)
