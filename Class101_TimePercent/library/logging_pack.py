import logging.handlers
import sys

# formatter 생성
# 로그 메시지의 형식을 지정합니다. 로그 레벨, 파일명, 라인 번호, 시간, 메시지를 포함하는 형식입니다.
formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s > %(message)s')

# logger 인스턴스를 생성 및 로그 레벨 설정
logger = logging.getLogger("crumbs")
logger.setLevel(logging.DEBUG)
# 로그 메시지를 콘솔에 출력하도록 설정한다.
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# user=getpass.getuser()
# print("user : " + str(user))
# logger.debug("sys.platform: " + sys.platform)

# 이 코드는 기본적으로 로그 메시지를 콘솔에 출력하도록 설정된 로거를 구성한다.
