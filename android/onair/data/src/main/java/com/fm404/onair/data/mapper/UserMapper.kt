package com.fm404.onair.data.mapper

import com.fm404.onair.data.remote.dto.auth.UserInfoDto
import com.fm404.onair.domain.model.auth.UserInfo

fun UserInfoDto.toDomain() = UserInfo(
    userId = userId,
    nickname = nickname,
    username = username,
    phoneNumber = phoneNumber,
    profilePath = profilePath,
    role = role
)