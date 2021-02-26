import sys
import os
import time
import datetime
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import re
import urllib
from urllib.parse import urlparse
import time
import schedule


import settings
import mylogger

# ログの定義
logger = mylogger.setup_logger(__name__)

def login(url, id, pw, id_sel, pw_sel, display):
    # chromeドライバーのパス
    chrome_path = "./driver/chromedriver.exe"

    # Selenium用オプション
    if display == '0':
        # 「0」が設定されている場合は、ブラウザを表示して実行する
        op = Options()
        op.add_argument("--disable-gpu")
        op.add_argument("--disable-extensions")
        op.add_argument("--proxy-server='direct://'")
        op.add_argument("--proxy-bypass-list=*")
        op.add_argument("--start-maximized")
        op.add_argument("--headless")
        #driver = webdriver.Chrome(chrome_options=op)
        driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=op)
    else:
        # 「0」以外の場合は、ブラウザを非表示にして実行する
        #driver = webdriver.Chrome()
        driver = webdriver.Chrome(executable_path=chrome_path)

    # ログインページアクセス
    driver.get(url)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, pw_sel))
    )
    driver.find_elements_by_css_selector(id_sel)[0].send_keys(id)
    driver.find_elements_by_css_selector(pw_sel)[0].send_keys(pw)
    driver.find_elements_by_css_selector(pw_sel)[0].send_keys(Keys.ENTER)

    return driver


def check_ticket_page(driver, url, limit, interval, ticket_dic, start_time):

    Mypage_manu_sel = "section#mypageMenu"
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, Mypage_manu_sel))
    )
    # チケット販売ページに遷移
    driver.get(url)

    # ループ処理
    count = 0

    # 監視するチケットのセレクトボックスのインデックス
    first_target_selectbox = next(iter(ticket_dic))

    logger.info("公開開始時間まで待機開始")
    print("公開開始時間まで待機開始")

    # 公開開始時間まで待機開始
    while True:
        now_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
        # print("現在時刻：" + now_time)
        # print("公開開始時刻：" + start_time)
        if now_time >= start_time:
            break

    logger.info("公開開始時間になったため、監視を開始")
    print("公開開始時間になったため、監視を開始")

    while True:
        check_flg = True

        # ターゲット出現を待機
        Ticket_sel = "section#ticket"
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, Ticket_sel))
        )
        Ticket_select_sel = "select.event_ticket_count.ticket_select"
        ticket_select_ele = []
        ticket_select_enable = None
        select_ticket_ele = driver.find_elements_by_css_selector(Ticket_select_sel)
        for ticket_key in ticket_dic.keys():
            ticket_select_enable = select_ticket_ele[int(ticket_key) - 1].is_enabled()
            if bool(ticket_select_enable):
                # 活性の場合、購入枚数を選択する
                select_ticket_ele = driver.find_elements_by_css_selector(Ticket_select_sel)
                select_ticket = Select(select_ticket_ele[int(ticket_key) - 1])
                select_ticket.select_by_value(ticket_dic[ticket_key])
                check_flg = False
                logger.info(ticket_key + "番目のチケットが選択完了")
            else:
                # 非活性の場合
                logger.info(ticket_key + "番目のチケットが選択できない状態")
                pass

        if check_flg:
            if count > int(limit):
                return False

            time.sleep(float(interval))
            count += 1
            # ページを再読み込み
            driver.refresh()
            continue

        BUY_BTN_sel = "button.register_input_submit"
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, BUY_BTN_sel))
        )
        # Waitで待っても「お申込み / 購入手続き」ボタンが押せないことがあるため、スリープを入れる
        time.sleep(0.1)
        buy_button = driver.find_elements_by_css_selector(BUY_BTN_sel)[0]
        driver.execute_script("arguments[0].click();", buy_button)
        return True


def pay_info_input(driver, conveni_index):

    logger.info("支払処理を開始")
    print("支払処理を開始")

    # 購入ボタン
    SUBMIT_btn_sel = "li#submit-btn > button"
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SUBMIT_btn_sel))
    )

    # 購入内容はあるか確認
    Conveni_btn_sel = "p#other_payment_method_select_img"
    if len(driver.find_elements_by_css_selector(Conveni_btn_sel)):
        # コンビニ決済ボタン
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, Conveni_btn_sel))
        )
        driver.find_elements_by_css_selector(Conveni_btn_sel)[0].click()

        # コンビニ選択
        Conveni_btn_sel = "select#cvs_select"
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, Conveni_btn_sel))
        )
        select_cvs_ele = driver.find_elements_by_css_selector(Conveni_btn_sel)
        select_cvs = Select(select_cvs_ele[0])
        select_cvs.select_by_index(conveni_index)

    # 同意チェックボックス
    Agreement_chkbox_sel = "input#agreement_check_lp"
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, Agreement_chkbox_sel))
    )
    driver.find_elements_by_css_selector(Agreement_chkbox_sel)[0].click()

    # 購入ボタン
    SUBMIT_btn_sel = "li#submit-btn > button"
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SUBMIT_btn_sel))
    )
    submit_button = driver.find_elements_by_css_selector(SUBMIT_btn_sel)[0]
    driver.execute_script("arguments[0].click();", submit_button)
    logger.info("購入するボタンをクリック")
    print("購入するボタンをクリックしました")
    # if PAY_CLICK_FLG == "1":
    #     logger.info("購入するボタンクリックフラグが「1：クリックする」のため、支払うボタンをクリック")
    #     print("購入するボタンクリックフラグが「1：クリックする」のため、支払うボタンをクリックします")
    #     submit_button = driver.find_elements_by_css_selector(SUBMIT_btn_sel)[0]
    #     driver.execute_script("arguments[0].click();", submit_button)
    # else:
    #     logger.info("購入するボタンクリックフラグが「0：クリックしない」のため、支払うボタンをクリックしない")
    #     print("購入するボタンクリックフラグが「0：クリックしない」のため、支払うボタンをクリックしません")


def expexpiration_date_check():
    import datetime
    now = datetime.datetime.now()
    expexpiration_datetime = now.replace(month=3, day=7, hour=12, minute=0, second=0, microsecond=0)
    logger.info("有効期限：" + str(expexpiration_datetime))
    if now < expexpiration_datetime:
        return True
    else:
        return False

def main_job():
    print(datetime.datetime.now())
    print("監視開始時間になったため、処理を開始します")
    logger.info("時刻：" + str(datetime.datetime.now()))
    logger.info("監視開始時間になったため、処理を開始")

    # ログインURL
    LOGIN_URL = "https://t.livepocket.jp/login"
    ID_sel = "input#email"
    PASS_sel = "input#password"

    # ログイン処理
    driver = login(LOGIN_URL, ID, PASS, ID_sel, PASS_sel, DISPLAY)

    ret = check_ticket_page(driver, TARGET_URL, LIMIT_COUNT, INTERVAL, ticket_dic, START_TIME)
    logger.debug("チケットページ監視結果：" + str(ret))

    global exit_flg

    if not ret:
        print("監視リトライ上限回数を超過したため、監視を終了します")
        logger.info("チケットページでの監視リトライ上限回数を超過したため、監視を終了")
        #sys.exit(0)
        exit_flg += 1
        driver.close()
        return

    # 決済処理
    pay_info_input(driver, CONVENI_STORE)
    logger.info("決済情報入力処理が完了")
    exit_flg +=2
    return


def check_value_empty(key_str, value_str):
    if value_str == None or value_str == "":
        # 値が存在しない場合
        raise ValueError("「" + key_str + "」の値が見つかりません。config.iniの設定を確認して下さい。")
    return

def check_value_date(key_str, date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y/%m/%d')
    except ValueError:
        # 日付として正しくない場合
        raise ValueError("「" + key_str + "」の日付の形式はyyyy/MM/ddの形式で記載して下さい。config.iniの設定を確認して下さい。")
    return

def check_value_time(key_str, time_str):
    try:
        datetime.datetime.strptime(time_str, '%H:%M:%S.%f')
    except ValueError:
        # 日付として正しくない場合
        raise ValueError("「" + key_str + "」の日付の形式は「hh:mm:ss.ffffff」の形式で記載して下さい。config.iniの設定を確認して下さい。")
    return

def check_value_decimal(key_str, value_str):
    if not value_str.isdecimal():
        # 値が存在しない場合
        raise ValueError("「" + key_str + "」は半角数字で記載して下さい。config.iniの設定を確認して下さい。")
    return


if __name__ == '__main__':

    try:
        logger.debug("------------------------------------------------------------------------------------------------------------")
        logger.debug("------------------------------------------------------------------------------------------------------------")
        logger.info("プログラム起動開始")

        # 有効期限チェック
        if not (expexpiration_date_check()):
            logger.info("有効期限切れため、プログラム起動終了")
            print("有効期限切れのため、処理を終了します")
            sys.exit(0)

        # タスク終了フラグ
        exit_flg = 0

        # -------------設定ファイル（基本情報）読み込み-------------
        logger.debug("INIファイルのDEFAULTセクション読み込み")
        config_default = settings.read_config('DEFAULT')

        ID_sel   = "input#session_email"
        PASS_sel = "input#session_password"

        # ブラウザ表示オプションの取得
        DISPLAY = config_default.get('DISPLAY')
        if DISPLAY == None or DISPLAY == "":
            # 値が存在しない場合
            DISPLAY = "0"

        # IDの取得
        ID = config_default.get('ID')
        check_value_empty('ID', ID)

        # パスワードの取得
        PASS = config_default.get('PASSWORD')
        check_value_empty('PASSWORD', PASS)

        # 監視対象のURL取得
        TARGET_URL = config_default.get('TARGET_URL')
        check_value_empty('TARGET_URL', TARGET_URL)

        # インターバルの取得
        INTERVAL = config_default.get('INTERVAL')
        check_value_empty('INTERVAL', INTERVAL)

        # リトライ上限数の取得
        LIMIT_COUNT = config_default.get('LIMIT_COUNT')
        check_value_empty('LIMIT_COUNT', LIMIT_COUNT)
        check_value_decimal('LIMIT_COUNT', LIMIT_COUNT)

        # 公開開始時間を取得
        START_TIME = config_default.get('START_TIME')
        check_value_empty('START_TIME', START_TIME)
        check_value_time('START_TIME', START_TIME)

        # 監視開始時間を取得（公開開始時間の1分前）
        # start_datetime = datetime.datetime.strptime(START_TIME, '%H:%M:%S')
        start_datetime = datetime.datetime.strptime(START_TIME, '%H:%M:%S.%f')
        monitor_datetime = start_datetime - datetime.timedelta(minutes=1)
        monitor_max_datetime = monitor_datetime + datetime.timedelta(seconds=5)
        # monitor_str = monitor_datetime.strftime('%H:%M:%S')
        monitor_str = monitor_datetime.strftime('%H:%M:%S.%f')
        monitor_max_str = monitor_max_datetime.strftime('%H:%M:%S.%f')

        # -------------設定ファイル（チケット情報）読み込み-------------
        logger.debug("INIファイルのTICKET_INFOセクション読み込み")
        config_ticketinfo = settings.read_config('TICKET_INFO')
        # チケット購入辞書（キー：購入チケットインデックス、値：購入チケット枚数）
        ticket_dic = {}

        for index in range(1, 30):
            ticket_num = config_ticketinfo.get('TICKET_NUM' + str(index))
            ticket_count = config_ticketinfo.get('TICKET_COUNT' + str(index))
            if ticket_num and ticket_count:
                check_value_decimal('TICKET_NUM' + str(index), ticket_num)
                check_value_decimal('TICKET_COUNT' + str(index), ticket_count)
                if not 1 <= int(ticket_count) <= 2:
                    raise ValueError("「TICKET_COUNT" + str(index) + "」は1か2を記載して下さい。config.iniの設定を確認して下さい。")
                ticket_dic[ticket_num] = ticket_count
                logger.debug("チケット情報（TICKET_NUM" + str(index) + "）：" + ticket_num)
                logger.debug("チケット情報（TICKET_COUNT" + str(index) + "）：" + ticket_count)
            else:
                continue

        if not len(ticket_dic):
            raise ValueError("購入対象のチケットがありません。config.iniの設定を確認して下さい。")

        # -------------設定ファイル（支払い情報）読み込み-------------
        logger.debug("INIファイルのPAYINFOセクション読み込み")
        config_payinfo = settings.read_config('PAYINFO')

        # 対象コンビニの読み込み
        CONVENI_STORE = config_payinfo.get('CONVENI_STORE')
        check_value_empty('CONVENI_STORE', CONVENI_STORE)
        check_value_decimal('CONVENI_STORE', CONVENI_STORE)
        if not 1 <= int(CONVENI_STORE) <= 5:
            raise ValueError("「CONVENI_STORE」は1～5を記載して下さい。config.iniの設定を確認して下さい。")

        # 購入するボタンクリックフラグ
        # PAY_CLICK_FLG = config_payinfo.get('PAY_CLICK_FLG')
        # if PAY_CLICK_FLG == None or PAY_CLICK_FLG == "":
        #     # 値が存在しない場合
        #     PAY_CLICK_FLG = "1"

        print("-----------------------------------------------------------------------------")
        print("起動します")
        logger.info("プログラム起動")
        logger.debug("公開開始時間：" + START_TIME)
        logger.debug("監視開始時間：" + monitor_str)
        logger.debug("インターバル：" + INTERVAL)
        logger.debug("リトライ上限回数：" + LIMIT_COUNT)
        logger.debug("監視対象URL：" + TARGET_URL)
        logger.debug("ブラウザの表示・非表示：" + DISPLAY)
        # logger.debug("支払いボタンクリックフラグ：" + PAY_CLICK_FLG)

        # schedule.every().day.at(monitor_str).do(main_job)

        logger.info("監視開始時間まで待機開始")

        while True:
            print("....監視開始時間まで待機中.....")
            # schedule.run_pending()
            time.sleep(1.0)
            now_time = datetime.datetime.now().strftime('%H:%M:%S.%f')
            if now_time >= monitor_str and now_time <= monitor_max_str:
                # print("現在時刻：" + now_time)
                # print("監視時刻：" + monitor_str)
                # logger.debug("現在時刻：" + now_time)
                # logger.debug("監視時刻：" + monitor_str)
                main_job()

                #『続行するには何かキーを押してください . . .』と表示させる
                os.system('PAUSE')
                sys.exit(0)

    except Exception as err:
        print("処理が失敗しました。")
        print(err)
        logger.error("処理が失敗しました。")
        logger.error(err)
        logger.error(traceback.format_exc())
        #『続行するには何かキーを押してください . . .』と表示させる
        os.system('PAUSE')
