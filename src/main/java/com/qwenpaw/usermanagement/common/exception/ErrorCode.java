package com.qwenpaw.usermanagement.common.exception;

/**
 * 错误码枚举
 */
public enum ErrorCode {

    // 用户相关
    USER_NOT_FOUND("USER_0005", "用户不存在"),
    USER_ALREADY_EXISTS("USER_0003", "用户已存在"),
    USER_STATUS_INVALID("USER_0001", "用户状态无效"),

    // 标签相关
    TAG_NOT_FOUND("USER_0006", "标签不存在"),
    TAG_ALREADY_EXISTS("USER_0003", "标签编码已存在"),
    TAG_CODE_DUPLICATE("USER_0003", "标签编码必须唯一"),

    // 绑定相关
    BINDING_ALREADY_EXISTS("USER_0004", "绑定关系已存在"),
    BINDING_NOT_FOUND("USER_0004", "绑定关系不存在"),

    // 分群相关
    GROUP_NOT_FOUND("USER_0007", "用户分群不存在"),
    GROUP_ALREADY_EXISTS("USER_0007", "用户分群已存在"),

    // 匹配相关
    MATCH_PARAM_INVALID("USER_0008", "匹配参数无效"),
    TAG_MATCH_FAILED("USER_0010", "标签匹配超时"),

    // 通用
    PARAM_ERROR("USER_0001", "参数错误"),
    SYSTEM_ERROR("SYSTEM_0001", "系统异常"),
    DATABASE_ERROR("SYSTEM_0010", "数据库操作异常");

    private final String code;
    private final String message;

    ErrorCode(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}
