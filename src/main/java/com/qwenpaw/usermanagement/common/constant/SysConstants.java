package com.qwenpaw.usermanagement.common.constant;

/**
 * 系统常量
 */
public final class SysConstants {

    public static final String CHARSET_UTF8 = "UTF-8";
    public static final String DATE_TIME_FORMAT = "yyyy-MM-dd HH:mm:ss";
    public static final int MAX_RETRY_TIMES = 3;

    private SysConstants() {
        throw new IllegalStateException("Utility class");
    }
}
