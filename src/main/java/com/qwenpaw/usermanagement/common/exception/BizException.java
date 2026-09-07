package com.qwenpaw.usermanagement.common.exception;

/**
 * 业务异常类
 */
public class BizException extends RuntimeException {

    private final String errorCode;
    private final Object[] params;

    public BizException(String errorCode) {
        super(errorCode);
        this.errorCode = errorCode;
        this.params = new Object[0];
    }

    public BizException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
        this.params = new Object[0];
    }

    public BizException(String errorCode, Object[] params) {
        super(errorCode);
        this.errorCode = errorCode;
        this.params = params;
    }

    public BizException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
        this.params = new Object[0];
    }

    public String getErrorCode() {
        return errorCode;
    }

    public Object[] getParams() {
        return params;
    }
}
