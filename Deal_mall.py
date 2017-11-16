# -*- coding: utf-8 -*-
import heapq
import numpy as np
import pandas as pd
import bottleneck
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.cross_validation import train_test_split
import re
import xgboost as xgb
from sklearn.cluster import KMeans
import time, datetime
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.grid_search import GridSearchCV
import pickle as pkl
from os.path import *

wname_2_idx = dict()
sname_2_idx = dict()
uname_2_idx = dict()

kmeans_model = ''


def data_hlper(sub_usr_df, sub_shop_df,df_user_infos):
    x_data = []
    y_data = []
    for index, row in sub_usr_df.iterrows():
        shop_id_num = len(sub_shop_df['shop_id'].drop_duplicates())
        #cluster_label = get_cluster_label(sub_shop_df, row['longitude_x'],row['latitude_x'], shop_id_num)
        cluster_label = get_list_k(df_usr_data,df_user_infos)
        top5_wifi_name, conn_w_n = get_wifi_top(wifi_str = row['wifi_infos'])
        time_point = get_time_point(row['time_stamp'])
        usr_id = us_name_2_idx(row['user_id'])
        x_data.append(np.concatenate([cluster_label, top5_wifi_name, conn_w_n, time_point, [usr_id]]))
        y_data.append(sf_name_2_idx(row['shop_id']))

    assert len(x_data) == len(y_data)
    return x_data, y_data

def get_list_k(user_infos,df_user_infos):
    # deal la_l0
    print('deal la_lo....')
    la = df_user_infos['longitude']
    lo = df_user_infos['latitude']
    path = 'kmeans_model.pkl'
    if not exists(path):
        la_lo = np.array(list(zip(la, lo)))
        kmeans_model = KMeans(n_clusters=1000, random_state=1).fit(la_lo)

        with open('kmeans_model.pkl', 'wb') as output:
            pkl.dump(kmeans_model, output)
    else:
        pkl_file = open('kmeans_model.pkl', 'rb')
        kmeans_model = pkl.load(pkl_file)
    user_la_lo =np.array(list(zip(user_infos['longitude_x'],user_infos['longitude_x'])))
    list_k = kmeans_model.predict(user_la_lo)
    return list(list_k)

def val_data_loader(sub_usr_df, sub_shop_df):
    x_data = []
    for index, row in sub_usr_df.iterrows():
        cluster_label = get_cluster_label(sub_shop_df, row['longitude'], row['latitude'])
        top5_wifi_name, conn_w_n = get_wifi_top(wifi_str=row['wifi_infos'])
        time_point = get_time_point(row['time_stamp'])
        usr_id = us_name_2_idx(row['user_id'])
        x_data.append(np.concatenate([cluster_label, top5_wifi_name, conn_w_n, time_point, [usr_id]]))
    return x_data


def get_cluster_label(xy_data, x_lo, y_la, shop_id_num=10):
    global kmeans_model
    if kmeans_model == '':
        X = np.array(list(zip(xy_data['mean_lo'].tolist(), xy_data['mean_la'].tolist())))
        kmeans = KMeans(n_clusters=int(shop_id_num * 0.4), random_state=0).fit(X)
        kmeans_model = kmeans
        return (kmeans.predict([[x_lo, y_la]]))
    else:
        return (kmeans_model.predict([[x_lo, y_la]]))

def get_wifi_top(wifi_str='', ntop=15):  # 获取wifi强度15的店铺编号
    str_list = wifi_str.split(';')
    wifi_ifos = np.array([x.strip(' ').split('|')[:3] for x in str_list])
    w_name = wifi_ifos[:, 0]  #     获取列表中的wifi 的名字
    w_value = [int(x) for x in wifi_ifos[:, 1]]
    w_state = wifi_ifos[:, 2]  # 连接状态
    if 'true' in w_state:
        connection_wifi_name = w_name[w_state.tolist().index('true')]
    else:
        connection_wifi_name = 'unkown'
    if len(wifi_ifos) > ntop:
        top_5_idx = bottleneck.argpartsort(-np.array(w_value), ntop)[:ntop]
        return wf_name_2_idx(w_name[top_5_idx]), wf_name_2_idx([connection_wifi_name])
    else:
        sort_idx = np.argsort(-np.array(w_value))
        w_name = w_name[sort_idx].tolist()
        w_name.extend(['b_null'] * (ntop - len(wifi_ifos)))
        return wf_name_2_idx(w_name), wf_name_2_idx([connection_wifi_name])

def get_time_point(time_stamp=''):
    rh = re.compile(r'[\d]+:[\d]+')  # 时间
    match_list_h = rh.findall(time_stamp)
    time_point = match_list_h[0].split(':')[0]
    rd = re.compile(r'[\d]+-[\d]+-[\d]+')  # 日期
    match_list_d = rd.findall(time_stamp)
    date_week = datetime.datetime(*[int(x) for x in match_list_d[0].split('-')]).weekday()
    return [time_point, date_week]

def wf_name_2_idx(w_name):
    w_idx = []
    for w in w_name:
        if w in wname_2_idx.keys():
            w_idx.append(wname_2_idx[w])
        else:
            wname_2_idx[w] = len(wname_2_idx)
            w_idx.append(wname_2_idx[w])
    return w_idx

def sf_name_2_idx(s_name):
    if s_name in sname_2_idx.keys():
        return sname_2_idx[s_name]
    else:
        sname_2_idx[s_name] = len(sname_2_idx)
        return sname_2_idx[s_name]


def us_name_2_idx(u_name):
    if u_name in uname_2_idx.keys():
        return uname_2_idx[u_name]
    else:
        uname_2_idx[u_name] = len(uname_2_idx)
        return uname_2_idx[u_name]

def train_xgb(x_data, y_data, ma_id):

    train_X, test_X, train_Y, test_Y = train_test_split(x_data, y_data, \
                                                        test_size=0.25, random_state=33)
    nclass = len(set(y_data))
    xg_train = xgb.DMatrix(train_X, label = train_Y)
    xg_test = xgb.DMatrix(test_X, label = test_Y)
    param = {}
    # use softmax multi-class classification
    param['objective'] = 'multi:softmax'
    # scale weight of positive examples
    param['eta'] = 0.1
    param['max_depth'] = 18
    param['silent'] = 1
    param['nthread'] = 6
    param['num_class'] = nclass

    watchlist = [(xg_train, 'train'), (xg_test, 'test')]
    num_round = 80
    bst = xgb.train(param, xg_train, num_round, watchlist)
    # get prediction
    pred = bst.predict(xg_test)
    acc = (sum(int(pred[i]) == test_Y[i] for i in range(len(test_Y)))/float(len(test_Y)))
    print('predicting, classification ' + str(ma_id) + ':acc=%f'%acc)
    return bst

    # if acc<0.9:
    #     #GBDT = GradientBoostingClassifier()
    #     param_test1 = {'n_estimators': range(20, 81, 10)}
    #     gsearch1 = GridSearchCV(estimator=GradientBoostingClassifier(learning_rate=0.1, min_samples_split=300,
    #                                                                  min_samples_leaf=20, max_depth=8,
    #                                                                  max_features='sqrt', subsample=0.8,
    #                                                                  random_state=10),
    #                             param_grid=param_test1,scoring='roc_auc', iid=False, cv=5)
    #     gsearch1.fit(train_X, train_Y)
    #     G_pre = gsearch1.predict(test_X)
    #     acc = (sum(int(G_pre[i]) == test_Y[i] for i in range(len(test_Y))) / float(len(test_Y)))
    #     print('GBDT predicting, classification ' + str(ma_id) + ':acc=%f'%acc)
    #     return gsearch1


def pred_xgb(x_test, bst, row_id):
    xg_test = xgb.DMatrix(x_test)
    pred = bst.predict(xg_test)
    idx_2_sname = dict(zip(sname_2_idx.values(), sname_2_idx.keys()))
    pred_shopid = [idx_2_sname[int(x)] for x in pred]
    resluts = list(zip(row_id.tolist(), pred_shopid))
    with open('result.csv', 'a') as f:
        for x, y in resluts:
            f.write(str(x) + ',' + str(y) + '\n')


if __name__ == '__main__':
    global kmeans_model
    with open('result.csv', 'w') as f:
        f.write('row_id,shop_id' + '\n')

    loc = pd.read_csv('shop_location.csv')
    df_user_infos = pd.read_csv('train-ccf_first_round_user_shop_behavior.csv')
    df_shop_infos = pd.read_csv('train-ccf_first_round_shop_info.csv')
    df_test = pd.read_csv('test-evaluation_public.csv')
    # 连接全表
    df_usr_data = pd.merge(df_user_infos, df_shop_infos, on=['shop_id'], how='left')
    df_shop_data = pd.merge(loc, df_shop_infos, on=['shop_id'], how='left')

    all_mallid = df_shop_infos['mall_id'].drop_duplicates()  # 所有的mall_id
    all_mallid = list(zip(range(1, len(all_mallid.tolist()) + 1), all_mallid.tolist()))
    for idx, ma_id in all_mallid:

        print(idx, len(all_mallid))
        sub_usr_df = df_usr_data[df_usr_data['mall_id'] == ma_id]
        sub_shop_df = df_shop_data[df_shop_data['mall_id'] == ma_id]
        sub_test_df = df_test[df_test['mall_id'] == ma_id]

        x_data, y_data = data_hlper(sub_usr_df, sub_shop_df,df_user_infos)
        x_test_data = val_data_loader(sub_test_df, sub_shop_df)

        bst = train_xgb(np.array(x_data).astype(float), np.array(y_data).astype(float), ma_id)

        pred_xgb(np.array(x_test_data), bst, sub_test_df['row_id'])

        wname_2_idx.clear()
        sname_2_idx.clear()
        uname_2_idx.clear()
        kmeans_model = ''
