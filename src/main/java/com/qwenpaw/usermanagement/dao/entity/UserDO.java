package com.qwenpaw.usermanagement.dao.entity;

import com.qwenpaw.usermanagement.common.model.BaseEntity;

/**
 * 用户数据对象
 */
public class UserDO extends BaseEntity {

    private String userId;
    private String nickname;
    private String avatarUrl;
    private Integer status;
    private Integer tagCount;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getNickname() {
        return nickname;
    }

    public void setNickname(String nickname) {
        this.nickname = nickname;
    }

    public String getAvatarUrl() {
        return avatarUrl;
    }

    public void setAvatarUrl(String avatarUrl) {
        this.avatarUrl = avatarUrl;
    }

    public Integer getStatus() {
        return status;
    }

    public void setStatus(Integer status) {
        this.status = status;
    }

    public Integer getTagCount() {
        return tagCount;
    }

    public void setTagCount(Integer tagCount) {
        this.tagCount = tagCount;
    }
}
