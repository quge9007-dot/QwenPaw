package com.qwenpaw.usermanagement.common.constant;

/**
 * 标签相关常量
 */
public final class TagConstants {

    public static final int TAG_LEVEL_ONE = 1;
    public static final int TAG_LEVEL_TWO = 2;
    public static final int TAG_STATUS_ENABLED = 1;
    public static final int TAG_STATUS_DISABLED = 0;

    public static final int MATCH_TYPE_ALL = 1;
    public static final int MATCH_TYPE_ANY = 2;

    public static final int BINDING_SOURCE_MANUAL = 1;
    public static final int BINDING_SOURCE_SYSTEM = 2;

    public static final int GROUP_MATCH_TYPE_ALL = 1;
    public static final int GROUP_MATCH_TYPE_ANY = 2;

    public static final int TAG_BINDING_MATCH_MODE_INCLUDE = 1;
    public static final int TAG_BINDING_MATCH_MODE_EXCLUDE = 2;

    private TagConstants() {
        throw new IllegalStateException("Utility class");
    }
}
