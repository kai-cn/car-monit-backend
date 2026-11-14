package com.ruoyi.common.config.serializer;

import java.util.Objects;
import tools.jackson.core.JsonGenerator;
import tools.jackson.databind.BeanProperty;
import tools.jackson.databind.SerializationContext;
import tools.jackson.databind.ValueSerializer;
import com.ruoyi.common.annotation.Sensitive;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.enums.DesensitizedType;
import com.ruoyi.common.utils.SecurityUtils;

/**
 * 数据脱敏序列化过滤
 *
 * <p>Jackson 3 迁移要点：{@code JsonSerializer} 更名为 {@link ValueSerializer}，
 * {@code SerializerProvider} 更名为 {@link SerializationContext}，
 * 上下文感知能力直接通过 ValueSerializer#createContextual 覆盖（不再需要 ContextualSerializer 接口）。</p>
 *
 * @author ruoyi
 */
public class SensitiveJsonSerializer extends ValueSerializer<String>
{
    private DesensitizedType desensitizedType;

    @Override
    public void serialize(String value, JsonGenerator gen, SerializationContext context)
    {
        if (desensitization())
        {
            gen.writeString(desensitizedType.desensitizer().apply(value));
        }
        else
        {
            gen.writeString(value);
        }
    }

    @Override
    public ValueSerializer<?> createContextual(SerializationContext context, BeanProperty property)
    {
        Sensitive annotation = property.getAnnotation(Sensitive.class);
        if (Objects.nonNull(annotation) && Objects.equals(String.class, property.getType().getRawClass()))
        {
            this.desensitizedType = annotation.desensitizedType();
            return this;
        }
        return context.findValueSerializer(property.getType());
    }

    /**
     * 是否需要脱敏处理
     */
    private boolean desensitization()
    {
        try
        {
            LoginUser securityUser = SecurityUtils.getLoginUser();
            // 管理员不脱敏
            return !securityUser.getUser().isAdmin();
        }
        catch (Exception e)
        {
            return true;
        }
    }
}
