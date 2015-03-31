from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.utils.http import urlsafe_base64_decode, is_safe_url
from django.views.generic import (DetailView, CreateView, UpdateView,
                                  TemplateView, View)

from brambling.forms.orders import AddCardForm
from brambling.forms.user import PersonForm, HomeForm, SignUpForm
from brambling.models import Person, Home, CreditCard
from brambling.tokens import token_generators
from brambling.mail import send_confirmation_email
from brambling.utils.payment import dwolla_can_connect, dwolla_customer_oauth_url, LIVE


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/sign_up.html'

    def get_success_url(self):
        redirect_to = self.request.GET.get('next', '/')
        if not is_safe_url(url=redirect_to, host=self.request.get_host()):
            redirect_to = '/'
        return redirect_to

    def get_form_kwargs(self):
        kwargs = super(SignUpView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs


def send_confirmation_email_view(request, *args, **kwargs):
    if not request.user.is_authenticated():
        raise Http404
    send_confirmation_email(request.user, site=get_current_site(request), secure=request.is_secure())
    messages.add_message(request, messages.SUCCESS, "Confirmation email sent.")
    return HttpResponseRedirect('/')


class EmailConfirmView(DetailView):
    model = Person
    generator = token_generators['email_confirm']
    template_name = 'brambling/email_confirm.html'

    def get_object(self):
        if 'pkb64' not in self.kwargs:
            raise AttributeError("pkb64 required.")
        try:
            pk = urlsafe_base64_decode(self.kwargs['pkb64'])
            return Person._default_manager.get(pk=pk)
        except (TypeError, ValueError, OverflowError, Person.DoesNotExist):
            raise Http404

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.generator.check_token(self.object, self.kwargs['token']):
            raise Http404("Token invalid or expired.")
        self.object.confirmed_email = self.object.email
        self.object.save()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class PersonView(UpdateView):
    model = Person
    form_class = PersonForm

    def get_object(self):
        if self.request.user.is_authenticated():
            return self.request.user
        raise Http404

    def get_form_kwargs(self):
        kwargs = super(PersonView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Profile saved.")
        return super(PersonView, self).form_valid(form)

    def form_invalid(self, form):
        return super(PersonView, self).form_invalid(form)

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super(PersonView, self).get_context_data(**kwargs)
        context.update({
            'cards': self.request.user.cards.order_by('-added'),
        })
        if dwolla_can_connect(self.object, LIVE):
            context['dwolla_oauth_url'] = dwolla_customer_oauth_url(
                self.request.user, LIVE, self.request)
        return context


class CreditCardAddView(TemplateView):
    template_name = 'brambling/creditcard_add.html'

    def post(self, request, *args, **kwargs):
        form = AddCardForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()

            if ('next_url' in request.GET and
                    is_safe_url(url=request.GET['next_url'],
                                host=request.get_host())):
                next_url = request.GET['next_url']
            else:
                next_url = reverse('brambling_user_profile')
            return HttpResponseRedirect(next_url)
        self.errors = form.errors['__all__']
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreditCardAddView, self).get_context_data(**kwargs)
        context.update({
            'STRIPE_PUBLISHABLE_KEY': getattr(settings,
                                              'STRIPE_PUBLISHABLE_KEY',
                                              ''),
            'errors': getattr(self, 'errors', {}),
        })
        return context


class CreditCardDeleteView(View):
    def success(self):
        return HttpResponse('')

    def delete(self, request, *args, **kwargs):
        if not request.is_ajax():
            raise Http404

        try:
            creditcard = CreditCard.objects.get(pk=kwargs['pk'])
        except CreditCard.DoesNotExist:
            # Count it a success.
            return self.success()

        user = request.user

        if creditcard.person_id != user.id:
            # Maybe also just redirect?
            raise Http404

        creditcard.delete()
        return self.success()

    def post(self, *args, **kwargs):
        return self.delete(*args, **kwargs)


class HomeView(UpdateView):
    model = Home
    form_class = HomeForm

    def get_object(self):
        if not self.request.user.is_authenticated():
            raise Http404
        return (Home.objects.filter(residents=self.request.user).first() or
                Home())

    def get_form_kwargs(self):
        kwargs = super(HomeView, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        return reverse('brambling_home')


class RemoveResidentView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404
        try:
            home = Home.objects.get(residents=self.request.user)
        except Home.DoesNotExist:
            pass
        else:
            try:
                person = Person.objects.get(pk=kwargs['pk'])
            except Person.DoesNotExist:
                pass
            else:
                home.residents.remove(person)
                if not home.residents.exists():
                    home.delete()
            messages.success(request, 'Removed resident successfully.')
        return HttpResponseRedirect(reverse('brambling_home'))
