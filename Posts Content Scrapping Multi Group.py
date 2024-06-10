import requests
import json
import re
import os
import re
from datetime import datetime


# Expression régulière pour extraire le nom de fichier avec son extension
patternImage = r'/([^/]+\.[a-zA-Z0-9]+)\?'
patternPdf = r'/([^/]+\.pdf)'

# Jeton d'accès (remplacez par votre propre jeton)
access_token = 'access-token'

# Paramètres de la requête
params = {
    'access_token': access_token,
    'fields': 'id,message,created_time, from, attachments,comments'
}
origin_download_path = 'Workplace_groups'

def get_all_groups():
    url = 'https://graph.facebook.com/v12.0/community/groups'
    params = {
        'access_token': access_token,
        'limit': 100,  # Limite le nombre de groupes par requête
        'fields': 'id,name,privacy'
    }
    groups = []
    while url:
        response = requests.get(url, params=params)
        data = response.json()
        if 'data' in data:
            groups.extend(data['data'])
            url = data.get('paging', {}).get('next')  # URL pour la page suivante
        else:
            url = None
            print("Erreur ou fin des résultats:", data)
    return groups

# Fonction pour nettoyer et tronquer les noms de fichier
def clean_filename(filename, max_length=255):
    # Remplace les caractères non alphanumériques par des underscores
    filename = re.sub(r'[^A-Za-z0-9_\-\.\\ ]', '_', filename)
    # Tronque le nom de fichier si nécessaire
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename


def get_all_posts(group_id, params):
    url = f'https://graph.facebook.com/v12.0/{group_id}/feed'

    all_posts = []

    while url:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()

            if 'data' in data:
                all_posts.extend(data['data'])

            # Pagination
            if 'paging' in data and 'next' in data['paging']:
                url = data['paging']['next']
            else:
                url = None
        else:
            print(f"Failed to fetch posts: {response.status_code}, {response.text}")

    return all_posts

def download_media(media_url, download_path, media_name):
    # Recherche du motif dans l'URL
    if media_url:
        # Télécharger le média
        media_response = requests.get(media_url)
        # print(media_url)
        print("media_response :   ", media_response)
        if media_response.status_code == 200:
            # Utiliser une partie de l'URL pour générer un nom de fichier unique et propre
            url_part = media_url.split('/')[-1].split('?')[0]
            # file_name = clean_filename(f"{post_id}_{url_part}") + media_name
            file_name = clean_filename(media_name)
            file_path = os.path.join(download_path, file_name)
            content = media_response.content

            with open(file_path, 'wb') as f:
                f.write(content)
            print(f"Downloaded: {file_path}")
        else:
            print(f"Failed to download media from {media_url}")


if not os.path.exists(origin_download_path):
    os.makedirs(origin_download_path)
    os.chdir(origin_download_path)
    print("=============== PATH1", origin_download_path)
# Faire la requête à l'API
# response = requests.get(url, params=params)
# Récupérer tous les groupes
all_groups = get_all_groups()

# Afficher les groupes récupérés
for group in all_groups:
    #download_path = origin_download_path + "/" + group['name']
    download_path = group['name']
    download_path = download_path.replace('/', '_').replace('\\', '_')
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    os.chdir(download_path)
    print("=============== PATH2", download_path)
    print(f"ID: {group['id']}, Name: {group['name']}, Privacy: {group['privacy']}")
    posts = get_all_posts(group['id'], params)

# Parcourir les posts
    for post in posts:
        #print(post)
        post_id = post['id']
        message = post.get('message', '')
        date = post.get('created_time', '')
        date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        formatted_date = date_obj.strftime("%Y_%m_%d")
        autor = post.get('from', {}).get('name', '')
        comments = post.get('comments', '')
        #download_path = origin_download_path + "/" + group['name']+ "/" + formatted_date + "_" + autor  + "_" + post_id
        download_path = formatted_date + "_" + autor + "_" + post_id
        print("=============== PATH3", download_path)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        file_name = clean_filename(f"{formatted_date}_{autor}_{post_id}.txt")
        txt_filepath = os.path.join(download_path, file_name)
        # Conversion du diction en json pour écrire dans le fichier les commentaires
        json_comments = json.dumps(comments, indent=4)
        with open(txt_filepath, 'w', encoding='utf-8') as txt_file:
            txt_file.write(message + "\n" + date + "\n"+"--------COMMENTS--------"+"\n" + json_comments)

        # Vérifier les pièces jointes
        attachments = post.get('attachments', {}).get('data', [])
        # print(attachments)
        i = 0
        for attachment in attachments:
            i = i + 1
            type = ''
            #print("Attachment: ", attachment)
            if attachment.get('type', '') == 'work_content_attachment':
                subattachments = attachment.get('subattachments', {}).get('data', {})
                for subattachment in subattachments:
                    media_url = subattachment.get('url', '')
                    media_name = subattachment.get('title', '')
                    # Dowload le media
                    download_media(media_url, download_path, media_name)
            elif attachment.get('type', '') == 'animated_image_share':
                media = attachment
                media_url= media.get('media', {}).get('source', '')
                extension = ".mp4"
                media_name = post_id + str(i) + extension
                download_media(media_url, download_path, media_name)
            elif attachment.get('type', '') == 'video_inline':
                media = attachment
                media_url = media.get('url', '')
                extension = ".mp4"
                media_name = post_id + str(i) + extension
                download_media(media_url, download_path, media_name)
            elif attachment.get('type', '') == 'photo':
                media = attachment
                #media_url = media.get('url', '')
                #extension = ".jpg"
                #media_name = post_id + str(i) + extension
                media_url = media.get('media', {}).get('image', {}).get('src', '')
                match = re.search(patternImage, media_url)
                media_name = match.group(1)
                download_media(media_url, download_path, media_name)
            elif attachment.get('type', '') == 'album':
                subattachments = attachment.get('subattachments', {}).get('data', {})
                for subattachment in subattachments:
                    media_url = subattachment.get('media', {}).get('image', {}).get('src', '')
                    match = re.search(patternImage, media_url)
                    media_name = match.group(1)
                    download_media(media_url, download_path, media_name)
            elif attachment.get('type', '') == 'share':
                text = attachment.get('title', '') + " : " + attachment.get('url', '')
                file_name = clean_filename(f"External_links_{autor}_{post_id}.txt")
                txt_filepath = os.path.join(download_path, file_name)
                with open(txt_filepath, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(text)
                #media_name = post_id + str(i) + extension
                #print('Url::::::::', media)
    os.chdir('..')
print("================END================")
