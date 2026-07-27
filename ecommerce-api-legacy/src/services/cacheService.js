'use strict';

const { CACHE_MAX_ENTRIES } = require('../config/constants');

/**
 * Cache em memória com limite de entradas e descarte FIFO.
 *
 * Substitui o objeto `globalCache` do módulo `utils`, que era estado global
 * compartilhado, sem limite e sem invalidação (vazamento de memória).
 */
class CacheService {
    constructor({ maxEntries = CACHE_MAX_ENTRIES, logger = console } = {}) {
        this.maxEntries = maxEntries;
        this.logger = logger;
        this.entries = new Map();
    }

    set(key, value) {
        if (this.entries.has(key)) this.entries.delete(key);
        this.entries.set(key, value);

        if (this.entries.size > this.maxEntries) {
            const oldest = this.entries.keys().next().value;
            this.entries.delete(oldest);
        }
        this.logger.log(`[cache] chave gravada: ${key}`);
    }

    get(key) {
        return this.entries.get(key);
    }
}

module.exports = CacheService;
