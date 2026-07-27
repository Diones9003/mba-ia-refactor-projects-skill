'use strict';

const serializers = require('../views/serializers');

/**
 * Orquestra o fluxo de `POST /api/checkout`.
 *
 * Só faz três coisas: lê a entrada já validada, chama o service e devolve a
 * resposta serializada. Nenhum SQL, nenhuma regra de pagamento, nenhum
 * tratamento de erro local (isso vai para o middleware central).
 */
class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
    }

    create = async (req, res) => {
        const result = await this.checkoutService.execute(req.validated.body);
        res.status(200).json(serializers.checkoutCreated(result));
    };
}

module.exports = CheckoutController;
