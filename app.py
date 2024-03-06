from flask import Flask, jsonify, request, render_template
import requests
from bs4 import BeautifulSoup
import datetime

app = Flask(__name__)
RESPONSE = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml')
LAST_UPDATE_DATE = datetime.datetime.strptime(RESPONSE.headers['Last-Modified'],
                                              '%a, %d %b %Y %H:%M:%S %Z') + datetime.timedelta(hours=3)


def fetch_currencies():
    soup = BeautifulSoup(RESPONSE.content, 'xml')
    currencies = soup.find_all('Currency')
    currency_list = [(currency.get('Kod'), currency.CurrencyName.text) for currency in currencies if
                     currency.get('Kod') and currency.get('Kod') != 'XDR']

    currency_list.append(('TRY', 'TÜRK LİRASI'))

    return currency_list


def fetch_currencies_with_rates():
    response = requests.get('https://www.tcmb.gov.tr/kurlar/today.xml')
    soup = BeautifulSoup(response.content, 'xml')
    currencies = soup.find_all('Currency')
    currency_list = [(currency.get('Kod'),
                      currency.CurrencyName.text, currency.ForexBuying.text, currency.ForexSelling.text) for currency in
                     currencies if
                     currency.get('Kod') and currency.get('Kod') != 'XDR']

    return currency_list


# Para birimlerini başlangıçta çek
currencies = fetch_currencies()
currency_with_rate = fetch_currencies_with_rates()


@app.route('/')
def home():
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
        converted_amount = amount / float(to_rate.ForexBuying.text)
    elif to_currency == 'TRY':
        converted_amount = amount * float(from_rate.ForexBuying.text)
    else:
        converted_amount = (amount / float(to_rate.ForexBuying.text)) * float(from_rate.ForexBuying.text)

    result = f'{amount} {from_currency} = {converted_amount:.2f} {to_currency}'

    # JSON olarak sonucu döndür
    return jsonify({'conversionResult': result})


if __name__ == '__main__':
    app.run(debug=True)
