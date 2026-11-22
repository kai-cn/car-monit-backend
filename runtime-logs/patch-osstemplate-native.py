#!/usr/bin/env python3

"""
@description 历史脚本 patch-osstemplate-native.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-osstemplate-native.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\OssTemplate.java')

t = p.read_text(encoding='utf-8')

start = '''\t@Override

\tpublic void afterPropertiesSet() {

'''

end = '''\t}

'''

i = t.index(start)

j = t.index(end, i) + len(end)

body = '''\t@Override

\tpublic void afterPropertiesSet() {

\t\ttry {

\t\t\tClientConfiguration clientConfiguration = new ClientConfiguration();

\t\t\tclientConfiguration.setMaxConnections(ossProperties.getMaxConnections());



\t\t\tAwsClientBuilder.EndpointConfiguration endpointConfiguration = new AwsClientBuilder.EndpointConfiguration(

\t\t\t\t\tossProperties.getEndpoint(), ossProperties.getRegion());

\t\t\tAWSCredentials awsCredentials = new BasicAWSCredentials(ossProperties.getAccessKey(),

\t\t\t\t\tossProperties.getSecretKey());

\t\t\tAWSCredentialsProvider awsCredentialsProvider = new AWSStaticCredentialsProvider(awsCredentials);

\t\t\tthis.amazonS3 = AmazonS3Client.builder().withEndpointConfiguration(endpointConfiguration)

\t\t\t\t\t.withClientConfiguration(clientConfiguration).withCredentials(awsCredentialsProvider)

\t\t\t\t\t.disableChunkedEncoding().withPathStyleAccessEnabled(ossProperties.getPathStyleAccess()).build();

\t\t} catch (Throwable t) {

\t\t\t// Native images cannot initialize AWS SDK v1 InternalConfig. Keep the bean alive

\t\t\t// so unrelated endpoints can start; OSS-backed endpoints remain unavailable in native.

\t\t\tSystem.err.println("OSS client initialization skipped: " + t.getClass().getSimpleName());

\t\t}

\t}

'''

p.write_text(t[:i] + body + t[j:], encoding='utf-8')

print('patched', 'OSS client initialization skipped' in p.read_text(encoding='utf-8'))

