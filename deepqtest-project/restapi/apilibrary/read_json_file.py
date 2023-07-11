import json


def load_restful_api(filename):
    json_file = open(filename, 'r')
    content = json_file.read()
    # print(content)
    restful_api = json.loads(content)
    # print(restful_api['status'][action_id])
    return restful_api


if __name__ == "__main__":
    api = load_restful_api('environment_configuration_apis.json')
    with open('README.md', 'w') as f:
        for a in api:
            # print(a, api[a]['API'])
            f.writelines('### {}. '.format(a) + api[a]['Description'] + '\n')
            f.writelines('#### ' + api[a]['API'] + '\n')
