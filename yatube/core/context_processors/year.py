import datetime


def year(request):
    current_year = datetime.datetime.now().year
    return {'year': current_year}
