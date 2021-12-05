from src.models.twitter_model import TweetPeopleModel, TweetPeopleResponseModel


def get_profile_endpoint(data):
    print(data)
    if data is None:
        return None

    profile = TweetPeopleModel(id=in_dict(data, 'id_str'), name=in_dict(data, 'name'),
                               screen_name=in_dict(data, 'screen_name'),
                               protected=in_dict_for_bool(data, 'protected'))
    profile.set_profile(profile_banner=in_dict(data, 'profile_banner_url'),
                        profile_image=remove_normal_from_user_image(in_dict(data, 'profile_image_url_https')),
                        profile_text_color=in_dict(data, 'profile_text_color'),
                        profile_sidebar_fill_color=in_dict(data, 'profile_sidebar_fill_color'),
                        profile_sidebar_border_color=in_dict(data, 'profile_sidebar_border_color'),
                        profile_link_color=in_dict(data, 'profile_link_color'))
    profile.set_description(location=in_dict(data, 'location'), description=in_dict(data, 'description'))
    profile.set_counters(followers_count=in_dict_for_int(data, 'followers_count'),
                         friends_count=in_dict_for_int(data, 'friends_count'),
                         favourites_count=in_dict_for_int(data, 'favourites_count'),
                         statuses_count=in_dict_for_int(data, 'statuses_count'))
    return profile


def get_profile_model_endpoint(data, count: int) -> TweetPeopleResponseModel:
    return TweetPeopleResponseModel(profile=get_profile_endpoint(data), count=count)


def in_dict(data, key):
    if data is None:
        return None
    return str(data[key]) if key in data else None


def in_dict_for_bool(data, key):
    if data is None:
        return None
    return bool(data[key]) if key in data else None


def in_dict_for_int(data, key):
    if data is None:
        return None
    return int(data[key]) if key in data else None


def remove_normal_from_user_image(url):
    return url.replace("_normal", "")


def get_profile_dict(key, value):
    return {
        'profile': {
            'profile_banner': in_dict(key, 'profile_banner_url'),
            'profile_image': remove_normal_from_user_image(in_dict(key, 'profile_image_url_https')),
            'profile_text_color': in_dict(key, 'profile_text_color'),
            'profile_sidebar_fill_color': in_dict(key, 'profile_sidebar_fill_color'),
            'profile_sidebar_border_color': in_dict(key, 'profile_sidebar_border_color'),
            'profile_link_color': in_dict(key, 'profile_link_color'),
            'id': in_dict(key, 'id_str'),
            'name': in_dict(key, 'name'),
            'screen_name': in_dict(key, 'screen_name'),
            'location': in_dict(key, 'location'),
            'description': in_dict(key, 'description'),
            'protected': in_dict(key, 'protected'),
            'followers_count': in_dict(key, 'followers_count'),
            'friends_count': in_dict(key, 'friends_count'),
            'favourites_count': in_dict(key, 'favourites_count'),
            'statuses_count': in_dict(key, 'statuses_count'),
        },
        'value': value
    }
