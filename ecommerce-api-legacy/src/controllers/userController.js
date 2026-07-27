'use strict';

const serializers = require('../views/serializers');

/** Orquestra o fluxo de `DELETE /api/users/:id`. */
class UserController {
    constructor(userService) {
        this.userService = userService;
    }

    remove = async (req, res) => {
        await this.userService.remove(req.validated.params.id);
        res.status(200).send(serializers.userDeleted());
    };
}

module.exports = UserController;
