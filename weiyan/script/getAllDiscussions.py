# -*- coding:utf-8 -*-
# vim:et:ts=4:sw=4:
#!/usr/bin/env python

import optparse
import requests
import pytz
from datetime import datetime
from slugify import slugify
from pathlib import Path

def stop_err(msg):
    sys.stderr.write('%s\n' % msg)
    sys.exit()

def gen_discussions_query(owner, repo_name, perPage, endCursor, first_n_threads):
    after_endCursor = ""
    if endCursor:
        after_endCursor = 'after: "%s"' % endCursor
    
    return f"""
    query {{
        repository(owner: "{owner}", name: "{repo_name}") {{
            discussions(
                orderBy: {{field: CREATED_AT, direction: DESC}}
                first: {perPage}
                {after_endCursor}) {{
                    nodes {{
                        title
                        number
                        url
                        createdAt
                        lastEditedAt
                        updatedAt
                        body
                        bodyText
                        bodyHTML
                        author {{
                            login
                        }}
                        category {{
                            name
                        }}
                        labels (first: 100) {{
                            nodes {{
                                name
                            }}
                        }} 
                        comments(first: {first_n_threads}) {{
                            nodes {{
                                body
                                author {{
                                    login
                                }}
                            }}
                        }}
                    }} # end nodes
                    pageInfo {{
                        hasNextPage
                        endCursor
                    }}
            }} # end discussions    
        }} # end discussions
    }} # end query
    """

def get_discussions(query, url, headers):
    response = requests.post(url, json={"query": query}, headers=headers)
    data = response.json()
    if data['data']['repository']['discussions'] is None:
        return ""
    else:
        return data['data']['repository']['discussions']

def __main__():
    usage  = "usage: python3 %prog [options] \n\nExample:\n"
    usage  = usage + "    python3 %prog -r <shenweiyan/Knowledge-Garden> -t <github token> -o out.txt"
    usage  = usage + "\n\nDescription:\n"
    usage  = usage + "    1. Fetch GitHub discussions data to mkdocs."
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-r', '--github_repo', help="GitHub repository name with namespace.")
    parser.add_option('-t', '--github_token', help='GitHub access token.')
    parser.add_option('-o', '--output', default='Discussions.txt', help='Output txt file (%default).')

    opts, args = parser.parse_args()
    gh_token   = opts.github_token
    gh_repo    = opts.github_repo
    outfile    = opts.output

    # 获取一个时区对象（例如，北京的时区）
    beijing_timezone = pytz.timezone('Asia/Shanghai')
    # 使用时区对象将当前时间转换为具有时区信息的时间
    beijing_time = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(beijing_timezone)

    gh_owner     = gh_repo.split("/")[0]
    gh_repo_name = gh_repo.split("/")[-1]

    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer %s" % gh_token}

    hasNextPage    = True
    allDiscussions = []
    endCursor      = ""  
    while hasNextPage:
        query          = gen_discussions_query(gh_owner, gh_repo_name, 5, endCursor, 10)
        results        = get_discussions(query, url, headers)
        discussions    = results['nodes']
        hasNextPage    = results['pageInfo']['hasNextPage']
        endCursor      = results['pageInfo']['endCursor']
        allDiscussions = allDiscussions + discussions

    # 保存所有的 Discussions 为 txt 格式
    discussionsDict = {'date': str(beijing_time), 'nodes': allDiscussions}
    with open(outfile, "w") as OUT:
        OUT.write(str(discussionsDict))
       
if __name__ == "__main__":
    __main__()
