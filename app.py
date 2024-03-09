from flask import Flask, jsonify, request, render_template
import requests
from bs4 import BeautifulSoup
import datetime

app = Flask(__name__)
RESPONSE = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml')
soup = BeautifulSoup(RESPONSE.content, 'xml')
CURRENCIES = soup.find_all('Currency')
LAST_UPDATE_DATE = datetime.datetime.strptime(RESPONSE.headers['Last-Modified'],
                                              '%a, %d %b %Y %H:%M:%S %Z') + datetime.timedelta(hours=3)


def fetch_currencies():
    currency_list = [(currency.get('Kod'), currency.CurrencyName.text) for currency in CURRENCIES if
                     currency.get('Kod') and currency.get('Kod') != 'XDR']

    currency_list.append(('TRY', 'TÜRK LİRASI'))

    return currency_list


def fetch_currencies_with_rates():
    currency_list = []
    for currency in CURRENCIES:
        if currency.get('Kod') and currency.get('Kod') != 'XDR':
            kod = currency.get('Kod')
            currency_name = currency.CurrencyName.text
            forex_buying = currency.ForexBuying.text
            forex_selling = currency.ForexSelling.text
            currency_list.append((kod, currency_name, forex_buying, forex_selling))

    return currency_list


@app.route('/')
def home():
    currencies = fetch_currencies()
    currency_with_rate = fetch_currencies_with_rates()
    return render_template('index.html', currencies=currencies,
                           currency_with_rate=currency_with_rate,
                           last_update=LAST_UPDATE_DATE)


@app.route('/convert', methods=['POST'])
def convert():
    data = request.get_json()

    amount = float(data['amount'])
    from_currency = data['from_currency']
    to_currency = data['to_currency']

    if amount <= 0:
        return jsonify({'conversionResult': 'Amount must be greater than 0'})

    # TCMB'nin güncel kurlarını içeren XML dosyasını çek
    response = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml')
    soup = BeautifulSoup(response.content, 'xml')

    # Gerekli döviz kurlarını bul

    from_rate = soup.find('Currency', {'Kod': from_currency})
    to_rate = soup.find('Currency', {'Kod': to_currency})

    # Dönüştürme işlemi yap
    if from_currency == 'TRY':
        if to_currency == 'TRY':
            result = f'{amount} {from_currency} = {amount} {to_currency}'
            return jsonify({'conversionResult': result})
        converted_amount = amount / float(to_rate.ForexBuying.text)
    elif to_currency == 'TRY':
        if from_currency == 'TRY':
            result = f'{amount} {from_currency} = {amount} {to_currency}'
            return jsonify({'conversionResult': result})
        converted_amount = amount * float(from_rate.ForexBuying.text)
    else:
        converted_amount = (amount / float(to_rate.ForexBuying.text)) * float(from_rate.ForexBuying.text)

    result = f'{amount} {from_currency} = {converted_amount:.2f} {to_currency}'

    # JSON olarak sonucu döndür
    return jsonify({'conversionResult': result})


if __name__ == '__main__':
    app.run(debug=True)
