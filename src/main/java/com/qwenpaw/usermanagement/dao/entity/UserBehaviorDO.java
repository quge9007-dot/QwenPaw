package com.qwenpaw.usermanagement.dao.entity;

import com.qwenpaw.usermanagement.common.model.BaseEntity;

/**
 * 用户行为数据对象
 */
public class UserBehaviorDO extends BaseEntity {

    private String userId;
    private String behaviorType;
    private String behaviorData;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getBehaviorType() {
        return behaviorType;
    }

    public void setBehaviorType(String behaviorType) {
        this.behaviorType = behaviorType;
    }

    public String getBehaviorData() {
        return behaviorData;
    }

    public void setBehaviorData(String behaviorData) {
        this.behaviorData = behaviorData;
    }
}
