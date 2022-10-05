import pandas as pd
import numpy as np
from tqdm import tqdm
import itertools
from datetime import timedelta
from zeeguu.core.model import User, UserActivityData, Language, UserLanguage, Article
from scipy import stats

def significance(p_val):
    return "*" if p_val < 0.01 else ""

languages_to_analyze = Language.CODES_OF_LANGUAGES_THAT_CAN_BE_LEARNED # [:-2]

def articles_correlations():
	all_users = User.find_all()
	print(len(all_users))


	for reading_language in languages_to_analyze:
		articles_df = pd.DataFrame(columns=["id", "lang", "difficulty", "word_count", "title_length", "opened", "translated", "spoken", "liked", "closed", 'avg_reading_time', 'std_reading_time', 'avg_reading_time_OOF', 'std_reading_time_OOF', 'avg_reading_time_firsttrans', 'std_reading_time_firsttrans', "feedback_difficulty_easy", "feedback_difficulty_ok", "feedback_difficulty_hard", "feedback_difficulty_too_hard"])

		#print("\nLANGUAGE:", reading_language)
		language_id = Language.find(reading_language).id
		print("\nLANGUAGE:", reading_language, language_id)
		reading_times = {}
		reading_times_OOF = {}
		reading_times_firsttrans = {}
		user_feedbacks = {}
		for user in tqdm(all_users):
			if user.learned_language_id == language_id:
				events = UserActivityData.find(user)
				# todo: check reading time with user reading session
				for event_idx, event in enumerate(events):
					article_id = event.article_id
					if article_id:
						if article_id != events[event_idx-1].article_id:
							lost_time = timedelta(seconds=0)
							out_of_focus_time = timedelta(seconds=0)
							first_translate_after = timedelta(seconds=0)
						article_data = Article.find_by_id(article_id)
						if article_data.language_id == language_id:
							if not (articles_df['id'] == article_id).any():
								title_len = len(article_data.title.split())
								df = {"id":article_id, "lang":reading_language, "difficulty":article_data.fk_difficulty, "word_count":article_data.word_count, "title_length":title_len, "opened":0, "translated":0, "spoken":0, "liked":0, "closed":0, 'feedback_difficulty_easy':0, 'feedback_difficulty_ok':0, 'feedback_difficulty_hard':0, 'feedback_difficulty_too_hard':0, 'avg_reading_time':0, 'std_reading_time':0, 'avg_reading_time_OOF':0, 'std_reading_time_OOF':0, 'avg_reading_time_firsttrans':0, 'std_reading_time_firsttrans':0}
								articles_df = articles_df.append(df, ignore_index = True)

							if event.event == "UMR - OPEN ARTICLE":
								articles_df.loc[articles_df.id == article_id, 'opened'] += 1
								open_time = event.time
							if event.event == "UMR - TRANSLATE TEXT" and event.value != '':
								if lost_time != timedelta(seconds=0):
									first_translate_after = first_translate_after
								else:
									first_translate_after = event.time - open_time
								articles_df.loc[articles_df.id == article_id, 'translated'] += 1
							if event.event == "UMR - SPEAK TEXT" and event.value != '':
								articles_df.loc[articles_df.id == article_id, 'spoken'] += 1
							if event.event == "UMR - LIKE ARTICLE":
								articles_df.loc[articles_df.id == article_id, 'liked'] += 1

							if event.event == "UMR - USER FEEDBACK":
								if event.value == "finished_difficulty_easy" or event.value == "finished_easy":
									articles_df.loc[articles_df.id == article_id, 'feedback_difficulty_easy'] += 1
								if event.value == "finished_difficulty_ok" or event.value == "finished_ok":
									articles_df.loc[articles_df.id == article_id, 'feedback_difficulty_ok'] += 1
								if event.value == "finished_difficulty_hard" or event.value == "finished_hard" or event.value == "finished_very_hard":
									articles_df.loc[articles_df.id == article_id, 'feedback_difficulty_hard'] += 1
								if event.value == "not_finished_for_too_difficult":
									articles_df.loc[articles_df.id == article_id, 'feedback_difficulty_too_hard'] += 1

							if event.event == "UMR - ARTICLE LOST FOCUS":
								lost_time = event.time
							if event.event == "UMR - ARTICLE FOCUSED":
								if lost_time != timedelta(seconds=0):
									out_of_focus = (event.time - lost_time)
								else:
									out_of_focus = timedelta(seconds=0)
								out_of_focus_time += out_of_focus
								lost_time = timedelta(seconds=0)

							if event.event == "UMR - ARTICLE CLOSED":
								articles_df.loc[articles_df.id == article_id, 'closed'] += 1
								close_time = event.time

								# (1) the full duration between opening and closing a text
								rt_full = (close_time - open_time).total_seconds()
								# set minimum reading time per article to 30 seconds. this is a random choice.
								if rt_full > 30.0:
									if article_id not in reading_times:
										reading_times[article_id] = [rt_full]
									else:
										reading_times[article_id].append(rt_full)

								# (2) the active time spent on a text, i.e., the duration between opening and closing a text minus any out-of-focus time spans
								rt_minus_lost_focus = (close_time - open_time - out_of_focus_time).total_seconds()
								if rt_minus_lost_focus > 30.0:
									if article_id not in reading_times_OOF:
										reading_times_OOF[article_id] = [rt_minus_lost_focus]
									else:
										reading_times_OOF[article_id].append(rt_minus_lost_focus)

								# (3) the number of seconds read before the first translation occurs
									if article_id not in reading_times_firsttrans:
										reading_times_firsttrans[article_id] = [first_translate_after.seconds]
									else:
										reading_times_firsttrans[article_id].append(first_translate_after.seconds)

								#reset out of focus to 0
								out_of_focus_time = timedelta(seconds=0)

		for art, times in reading_times.items():
			articles_df.loc[articles_df.id == art, 'avg_reading_time'] = np.mean(times)
			articles_df.loc[articles_df.id == art, 'std_reading_time'] = np.std(times)

		for art, times in reading_times_OOF.items():
			articles_df.loc[articles_df.id == art, 'avg_reading_time_OOF'] = np.mean(times)
			articles_df.loc[articles_df.id == art, 'std_reading_time_OOF'] = np.std(times)

		for art, times in reading_times_firsttrans.items():
			articles_df.loc[articles_df.id == art, 'avg_reading_time_firsttrans'] = np.mean(times)
			articles_df.loc[articles_df.id == art, 'std_reading_time_firsttrans'] = np.std(times)

		print("Articles:", len(articles_df))

		correlation_variables = ["word_count", "difficulty", "liked", "translated", "spoken", "opened", "closed", "title_length", "avg_reading_time"]#, "avg_reading_time_OOF", "avg_reading_time_firsttrans"]
		for x in itertools.combinations(correlation_variables, 2):
		    spearman_corr = stats.spearmanr(articles_df[x[0]], articles_df[x[1]])
		    print(x[0], x[1], spearman_corr[0], significance(spearman_corr[1]))
		print("\n\n")

		articles_df.to_csv("articles-"+reading_language+"-2022-Jul-4.csv")


def users_correlations():
    users_reading_time = {}
    users_df = pd.DataFrame(columns=["id", "reading_lang", "native_lang", "opened", "translated", "spoken", "liked", "closed", 'translated_phrases', 'spoken_phrases', "feedback_difficulty_easy", "feedback_difficulty_ok", "feedback_difficulty_hard", "feedback_difficulty_too_hard"])
    all_users = User.find_all()
    print(len(all_users))

    for user in tqdm(all_users):

        df = {"id":user.id, "reading_lang":str(user.learned_language), "native_lang":str(user.native_language), "opened":0, "translated":0, "spoken":0, "liked":0, "closed":0, 'translated_phrases':[], 'spoken_phrases':[]}
        users_df = users_df.append(df, ignore_index = True)

        # todo: check all possible events
        events = UserActivityData.find(user)
        translated_phrases = []
        spoken_phrases = []
        reading_times = []
        for event in events:
            article_id = event.article_id
            if article_id:
                #print(article_id)
                if event.event == "UMR - OPEN ARTICLE":
                    users_df.loc[users_df.id == user.id, 'opened'] += 1
                    open_time = event.time
                if event.event == "UMR - TRANSLATE TEXT" and event.value != '':
                    translated_phrases.append(event.value)
                    users_df.loc[users_df.id == user.id, 'translated'] += 1
                if event.event == "UMR - SPEAK TEXT" and event.value != '':
                    spoken_phrases.append(event.value)
                    users_df.loc[users_df.id == user.id, 'spoken'] += 1
                if event.event == "UMR - LIKE ARTICLE":
                    users_df.loc[users_df.id == user.id, 'liked'] += 1

                if event.event == "UMR - USER FEEDBACK":
                    if event.value == "finished_difficulty_easy" or event.value == "finished_easy":
                        users_df.loc[users_df.id == user.id, 'feedback_difficulty_easy'] += 1
                    if event.value == "finished_difficulty_ok" or event.value == "finished_ok":
                        users_df.loc[users_df.id == user.id, 'feedback_difficulty_ok'] += 1
                    if event.value == "finished_difficulty_hard" or event.value == "finished_hard" or event.value == "finished_very_hard":
                        users_df.loc[users_df.id == user.id, 'feedback_difficulty_hard'] += 1
                    if event.value == "not_finished_for_too_difficult":
                        users_df.loc[users_df.id == user.id, 'feedback_difficulty_too_hard'] += 1

                if event.event == "UMR - ARTICLE CLOSED":
                    users_df.loc[users_df.id == user.id, 'closed'] += 1
                    close_time = event.time
                    rt = (close_time - open_time).total_seconds()
                    # set minimum reading time per article to 60 seoncds. this is a random choice
                    if rt > 60.0: reading_times.append(rt)

        user_idx = users_df.index[users_df['id'] == user.id].tolist()[0]
        users_df.at[user_idx, 'translated_phrases'] = translated_phrases
        users_df.at[user_idx, 'spoken_phrases'] = spoken_phrases
        users_df.at[user_idx, 'avg_reading_time'] = np.mean(reading_times)

        users_reading_time[user_idx] = reading_times

    # keep only users that opened at least 1 article
    users_df.drop(users_df[users_df.opened < 1].index, inplace=True)
    users_df['translated_normalized'] = users_df['translated'] /users_df['opened']
    users_df['spoken_normalized'] = users_df['spoken'] /users_df['opened']

    correlation_variables = ["opened", "translated", "spoken", "liked", "closed", 'avg_reading_time', "feedback_difficulty_easy", "feedback_difficulty_ok", "feedback_difficulty_hard", "feedback_difficulty_too_hard"]
    for x in itertools.combinations(correlation_variables, 2):
        spearman_corr = stats.spearmanr(users_df[x[0]], users_df[x[1]])
        print(x[0], x[1], spearman_corr[0], significance(spearman_corr[1]))
    print("\n\n")

    # keep only users with native lang is NOT English (because this is the default value and will therefore contain many false positives)
    print(users_df['native_lang'].value_counts())
    print("---")
    users_df.drop(users_df[users_df.native_lang == "<Language 'en'>"].index, inplace=True)

    rt = pd.DataFrame.from_dict(users_reading_times) 
    rt.to_csv('user_reading_times.csv', index = False, header=False)

    print("Users:", len(users_df))
    users_df.to_csv("users-2022-Jul-4.csv")


    print(print(users_df['reading_lang'].value_counts()))


if __name__== "__main__":
	articles_correlations()
	users_correlations()
