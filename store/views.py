from django.shortcuts import render, get_object_or_404
from .models import Article, Receipt, Issue

# Dashboard view (home)
def home(request):
    return render(request, 'store/dashboard.html')

# List all articles
def article_list(request):
    articles = Article.objects.all()
    return render(request, 'store/article_list.html', {'articles': articles})

# View a single article and its records
def article_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    receipts = Receipt.objects.filter(article=article)
    issues = Issue.objects.filter(article=article)
    return render(request, 'store/article_detail.html', {
        'article': article,
        'receipts': receipts,
        'issues': issues,
    })
