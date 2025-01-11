import math
from flask import Flask, request, jsonify, render_template
import pandas as pd
from flask_cors import CORS  # CORS modülünü ekleyin

app = Flask(__name__)

# CORS'u etkinleştirin, tüm origin'lere izin verir.
CORS(app, resources={r"/api/*": {"origins": "*"}})

# NaN ve None değerleri kontrol eden fonksiyon
def safe_get_value(value):
    if value is None or isinstance(value, float) and math.isnan(value):
        return ""  # Eğer None veya NaN ise, boş bir string döndürelim
    return value

# CSV dosyalarını yükleyelim
movies_df = pd.read_csv('movies_metadata.csv', low_memory=False)
credits_df = pd.read_csv('credits.csv', low_memory=False)
keywords_df = pd.read_csv('keywords.csv', low_memory=False)

# 'id' sütunlarını str (string) türüne dönüştürelim
movies_df['id'] = movies_df['id'].astype(str)
credits_df['id'] = credits_df['id'].astype(str)
keywords_df['id'] = keywords_df['id'].astype(str)

# Veri çerçevelerini birleştirelim
movies_with_credits_df = pd.merge(movies_df, credits_df, on='id', how='left')
movies_with_all_info_df = pd.merge(movies_with_credits_df, keywords_df, on='id', how='left')

# Cast sütununu işleyerek oyuncu isimlerini alalım
def get_cast_names(cast_column):
    try:
        cast_list = eval(cast_column)  # string'i listeye dönüştürür
        cast_names = [actor['character'] for actor in cast_list[:5]]
        return ', '.join(cast_names)
    except:
        return ''

# Keywords sütununu işleyerek anahtar kelimeleri alalım
def get_keywords(keywords_column):
    try:
        keywords_list = eval(keywords_column)  # string'i listeye dönüştürür
        keywords = [keyword['name'] for keyword in keywords_list[:5]]
        return ', '.join(keywords)
    except:
        return ''

# Cast ve Keywords sütunlarını düzenleyelim
movies_with_all_info_df['cast'] = movies_with_all_info_df['cast'].apply(get_cast_names)
movies_with_all_info_df['keywords'] = movies_with_all_info_df['keywords'].apply(get_keywords)

@app.route('/')
def index():
    # Ana sayfa için basit bir HTML formu
    return render_template('index.html')

@app.route('/api/film-onerisi', methods=['POST'])
def film_onerisi():
    # Kullanıcıdan gelen veriyi alalım
    user_data = request.json
    tur = user_data.get("tur")
    yil = user_data.get("yil")

    # Tür ve Yıl bilgisi kontrolü
    if not tur or not yil:
        return jsonify({"error": "Tür ve Yıl bilgisi eksik!"}), 400

    # Tür ve Yıla göre filtreleme yapalım
    filtered_movies = movies_with_all_info_df[
        (movies_with_all_info_df['genres'].str.contains(tur, case=False, na=False)) & 
        (movies_with_all_info_df['release_date'].str.contains(str(yil), na=False))
    ]

    # Eğer film bulunmazsa
    if filtered_movies.empty:
        return jsonify({"error": "Film bulunamadı!"}), 404

    # Bulunan filmleri formatlayalım
    film_list = []
    for _, movie in filtered_movies.iterrows():
        film_data = {
            "title": movie["title"],
            "release_date": safe_get_value(movie["release_date"]),
            "genres": safe_get_value(movie["genres"]),
            "overview": safe_get_value(movie["overview"]),
            "cast": safe_get_value(movie["cast"]),
            "keywords": safe_get_value(movie["keywords"])
        }
        film_list.append(film_data)

    # JSON yanıtını döndürelim
    return jsonify({
        "message": f"{tur} türünde, {yil} yılına ait filmler:",
        "films": film_list
    })

if __name__ == '__main__':
    app.run(debug=True)
