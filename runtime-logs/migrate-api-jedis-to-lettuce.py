#!/usr/bin/env python3
"""把 api 仓库所有 Java 分支的 Jedis 依赖与调用迁移到 Lettuce。

思路：
1. 先确认 API 侧直接使用 JedisCluster 的代码点：RedisSourceFactory 与
   SysUtilServiceImpl；仅替换依赖无法编译，必须同步改代码。
2. 新增 LettuceClusterClient 适配器，保留原调用方需要的 get(key) 语义，
   并把 RedisURI/Jedis HostAndPort 的转换集中在一个地方。
3. 把 pro-base-common/pom.xml 中的 redis.clients:jedis 替换为 Spring Boot
   starter-data-redis（由 BOM 管理版本，底层默认 Lettuce）。
4. 逐分支通过 GitHub API 提交，幂等：已存在适配器时跳过新增。

风险：Lettuce 连接创建后立即建立连接；若配置无有效节点会抛异常，
行为与原 JedisCluster 构造失败一致。此脚本不删分支、不 force push。
"""
import base64, json, re, sys, urllib.request
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

REPO = 'kai-cn/car-monit-api'
BRANCHES = ['master','car-monit-api-java-V3','car-monit-api-java-fix',
            'car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25',
            'feature/springboot3','feature/springboot3-jdk17','feature-dbupgrade']
H = {'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json',
     'X-GitHub-Api-Version':'2022-11-28','User-Agent':'jedis-to-lettuce'}

LETTUCE_CLIENT = '''package com.ruoyi.common.core.redis;

import io.lettuce.core.RedisURI;
import io.lettuce.core.cluster.RedisClusterClient;
import io.lettuce.core.cluster.api.sync.RedisClusterCommands;

import java.util.Set;

/** Minimal Lettuce replacement for the previously used JedisCluster read API. */
public class LettuceClusterClient implements AutoCloseable {
    private final RedisClusterClient client;
    private final RedisClusterCommands<String, String> commands;

    public LettuceClusterClient(Set<RedisURI> nodes) {
        this.client = RedisClusterClient.create(nodes);
        this.commands = client.connect().sync();
    }

    public String get(String key) {
        return commands.get(key);
    }

    @Override
    public void close() {
        commands.getStatefulConnection().close();
        client.shutdown();
    }
}
'''

REDIS_FACTORY = '''package com.ruoyi.common.core.redis;

import io.lettuce.core.RedisURI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.Serializable;
import java.util.HashSet;
import java.util.Set;

@Service
public class RedisSourceFactory implements Serializable {
    private static final long serialVersionUID = 1L;
    private static final Logger logger = LoggerFactory.getLogger(RedisSourceFactory.class);

    public LettuceClusterClient createSource(RedisConfig redisConfig) {
        if (redisConfig == null || redisConfig.getClusterNodes() == null || redisConfig.getClusterNodes().isEmpty()) {
            logger.error("Redis cluster node address 'cluster.nodes' is not configured.");
            throw new IllegalStateException("Redis cluster node address 'cluster.nodes' is not configured.");
        }

        Set<RedisURI> nodes = new HashSet<>();
        for (String node : redisConfig.getClusterNodes().split(",")) {
            String[] hp = node.trim().split(":");
            if (hp.length == 2) {
                try {
                    nodes.add(RedisURI.create(hp[0], Integer.parseInt(hp[1])));
                    logger.info("Added Redis node: " + node);
                } catch (NumberFormatException e) {
                    logger.warn("Invalid port number for Redis node: " + node + ". This node will be skipped.", e);
                }
            } else {
                logger.warn("Invalid node format (expected host:port): " + node + ". This node will be skipped.");
            }
        }
        if (nodes.isEmpty()) {
            throw new IllegalStateException("No valid Redis cluster nodes configured.");
        }

        try {
            LettuceClusterClient client = new LettuceClusterClient(nodes);
            logger.info("Lettuce cluster client created successfully with nodes: " + nodes);
            return client;
        } catch (Exception e) {
            logger.error("Failed to create Lettuce cluster client", e);
            throw e;
        }
    }
}
'''

JEDIS_DEP = re.compile(
    r'<dependency>\s*<groupId>redis\.clients</groupId>\s*<artifactId>jedis</artifactId>\s*(?:<version>[^<]*</version>\s*)?</dependency>',
    re.S)
LETTUCE_DEP = '''<dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>'''

def api(u, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(u, data=data, headers=H, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def put(br, path, text, sha, msg):
    api(f'https://api.github.com/repos/{REPO}/contents/{path}', 'PUT', {
        'message': msg, 'content': base64.b64encode(text.encode()).decode(), 'sha': sha, 'branch': br})

for br in BRANCHES:
    br_enc = br.replace('/','%2F')
    base = f'https://api.github.com/repos/{REPO}/contents'
    touched = []
    # pom changes
    for path in ['pom.xml','pro-base-common/pom.xml']:
        try:
            obj=api(f'{base}/{path}?ref={br_enc}')
        except Exception as e:
            print('FETCH_FAIL',br,path,e); continue
        t=base64.b64decode(obj['content']).decode('utf-8')
        n=t
        n=re.sub(r'\s*<jedis\.version>[^<]*</jedis\.version>', '', n)
        n=JEDIS_DEP.sub(LETTUCE_DEP, n)
        if n!=t:
            put(br,path,n,obj['sha'],'build: replace Jedis with Boot-managed Lettuce starter')
            touched.append(path)
    # code changes
    paths=['pro-base-common/src/main/java/com/ruoyi/common/core/redis/RedisSourceFactory.java',
           'pro-business-api/src/main/java/com/ruoyi/base/service/impl/SysUtilServiceImpl.java']
    for path in paths:
        try:
            obj=api(f'{base}/{path}?ref={br_enc}')
        except Exception as e:
            print('FETCH_FAIL',br,path,e); continue
        t=base64.b64decode(obj['content']).decode('utf-8')
        n=t
        if path.endswith('RedisSourceFactory.java'):
            n=REDIS_FACTORY
        else:
            n=n.replace('import redis.clients.jedis.JedisCluster;',
                        'import com.ruoyi.common.core.redis.LettuceClusterClient;')
            n=n.replace('JedisCluster','LettuceClusterClient')
        if n!=t:
            put(br,path,n,obj['sha'],'refactor(redis): migrate JedisCluster calls to Lettuce')
            touched.append(path)
    # new client class
    new_path='pro-base-common/src/main/java/com/ruoyi/common/core/redis/LettuceClusterClient.java'
    try:
        api(f'{base}/{new_path}?ref={br_enc}')
        exists=True
    except Exception:
        exists=False
    if not exists:
        api(f'{base}/{new_path}', 'PUT', {
            'message':'feat(redis): add Lettuce cluster client adapter',
            'content':base64.b64encode(LETTUCE_CLIENT.encode()).decode(),'branch':br})
        touched.append(new_path)
    print('UPDATED',br,','.join(touched) if touched else 'none')
