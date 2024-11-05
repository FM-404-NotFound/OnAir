package com.fm404.onair.domain.repository.broadcast

import com.fm404.onair.domain.model.broadcast.Broadcast

interface BroadcastRepository {
    suspend fun getBroadcastList(): Result<List<Broadcast>>
}