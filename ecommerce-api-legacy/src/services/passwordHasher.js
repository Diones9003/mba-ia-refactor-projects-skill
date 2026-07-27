'use strict';

const crypto = require('crypto');
const { promisify } = require('util');

const { PASSWORD_HASH } = require('../config/constants');

const scrypt = promisify(crypto.scrypt);

/**
 * Hash de senha com scrypt + salt por usuário.
 *
 * Substitui a função `badCrypto`, que concatenava base64 10.000 vezes e
 * truncava o resultado em 10 caracteres — determinística, sem salt e
 * trivialmente colidível.
 */
class PasswordHasher {
    constructor({ saltBytes, keyLength } = {}) {
        this.saltBytes = saltBytes ?? PASSWORD_HASH.SALT_BYTES;
        this.keyLength = keyLength ?? PASSWORD_HASH.KEY_LENGTH;
    }

    /** Formato armazenado: `scrypt$<salt-hex>$<derivado-hex>`. */
    async hash(password) {
        if (typeof password !== 'string' || password === '') {
            throw new Error('PasswordHasher.hash exige uma senha não vazia');
        }
        const salt = crypto.randomBytes(this.saltBytes).toString('hex');
        const derived = await scrypt(password, salt, this.keyLength);
        return `${PASSWORD_HASH.ALGORITHM}$${salt}$${derived.toString('hex')}`;
    }

    async verify(password, stored) {
        const [algorithm, salt, expected] = String(stored).split('$');
        if (algorithm !== PASSWORD_HASH.ALGORITHM || !salt || !expected) return false;

        const derived = await scrypt(password, salt, expected.length / 2);
        return crypto.timingSafeEqual(Buffer.from(expected, 'hex'), derived);
    }

    /**
     * Senha aleatória para contas criadas sem senha no checkout. O legado caía
     * em uma senha padrão fixa e conhecida em toda conta criada assim.
     */
    generateRandomPassword() {
        return crypto.randomBytes(PASSWORD_HASH.GENERATED_PASSWORD_BYTES).toString('base64url');
    }
}

module.exports = PasswordHasher;
