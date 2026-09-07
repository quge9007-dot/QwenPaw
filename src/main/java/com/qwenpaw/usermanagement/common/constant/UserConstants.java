package com.qwenpaw.usermanagement.common.constant;

/**
 * 用户相关常量
 */
public final class UserConstants {

    public static final int USER_STATUS_NORMAL = 1;
    public static final int USER_STATUS_DISABLED = 0;

    public static final int DEFAULT_PAGE_SIZE = 20;
    public static final int MAX_PAGE_SIZE = 100;

    public static final String USER_ID_PREFIX = "USR";

    private UserConstants() {
        throw new IllegalStateException("Utility class");
    }
}
