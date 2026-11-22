#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-osstemplate-native.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
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
