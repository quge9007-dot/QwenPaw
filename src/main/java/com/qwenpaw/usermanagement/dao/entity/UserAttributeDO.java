package com.qwenpaw.usermanagement.dao.entity;

import com.qwenpaw.usermanagement.common.model.BaseEntity;

/**
 * 用户属性数据对象
 */
public class UserAttributeDO extends BaseEntity {

    private String userId;
    private String attrKey;
    private String attrValue;
    private Integer attrType;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getAttrKey() {
        return attrKey;
    }

    public void setAttrKey(String attrKey) {
        this.attrKey = attrKey;
    }

    public String getAttrValue() {
        return attrValue;
    }

    public void setAttrValue(String attrValue) {
        this.attrValue = attrValue;
    }

    public Integer getAttrType() {
        return attrType;
    }

    public void setAttrType(Integer attrType) {
        this.attrType = attrType;
    }
}
