import chai, { expect } from 'chai';
import chaiAsPromised from 'chai-as-promised';
import { SinonStub, stub } from 'sinon';
import {
  setLoggedInElementsVisibility,
  logout,
  readCredentials,
  parseApiResponse,
  parseJsonResponse,
  fetchAllData,
  ajaxRequest,
  buttons,
  ApiResponse,
  Instance,
  RowData,
  AjaxParms,
  login,
} from '../src/index';

const jsdon = require('jsdom');

chai.use(chaiAsPromised);

describe('index tests', () => {
  let dataView: any;
  let loginLink: any;
  let apiResponse: Response;
  let jsonResponse: ApiResponse;
  let exampleInstance: Instance;
  let exampleRow: RowData;
  let fetchStub: SinonStub<any>;
  let mockAjaxParams: AjaxParms;
  let ajaxSuccessStub: SinonStub<any>;

  beforeEach(() => {
    const { JSDOM } = jsdon;
    global.window = new JSDOM(`<!DOCTYPE html>
      <body>
        <a id="loginLink">Login</a>
        <div id="dataView" hidden>
          <table id="table">
          </table>
        </div>
      </body>`).window;
    global.document = global.window.document;
    fetchStub = stub();
    global.fetch = fetchStub;

    dataView = document.getElementById('dataView');
    loginLink = document.getElementById('loginLink');

    process.env.API_DOMAIN = 'https://api.example.com';
    process.env.LOGIN_URL = 'https://cognito';
    exampleInstance = {
      Name: 'i-2',
      Id: 'i-2',
      Type: 'large',
      State: 'stopped',
      AZ: 'us-east-1',
      PublicIps: [],
      PrivateIps: [],
    };

    jsonResponse = {
      Instances: [
        {
          Name: 'Name',
          Id: 'i-1',
          Type: 'small',
          State: 'running',
          AZ: 'us-east-1',
          PublicIps: ['192.168.0.1', '192.168.0.2'],
          PrivateIps: ['8.8.8.8'],
        },
        exampleInstance,
      ],
    };

    exampleRow = {
      ...exampleInstance,
      PublicIps: '',
      PrivateIps: '',
    };

    apiResponse = {
      ok: true,
      status: 200,
      json: async () => jsonResponse,
    } as Response;

    ajaxSuccessStub = stub();
    mockAjaxParams = {
      success: ajaxSuccessStub,
    };
  });

  after(() => {
    delete process.env.API_DOMAIN;
    delete process.env.LOGIN_URL;
  });

  it('setLoggedInElementsVisibility works as expected', async () => {
    setLoggedInElementsVisibility(true);
    expect(dataView.hidden).eq(false);
    expect(loginLink.hidden).eq(true);
  });

  it('logout works as expected', async () => {
    localStorage.setItem('Authorization', 'Hunter1');
    setLoggedInElementsVisibility(true);

    logout();

    expect(dataView.hidden).eq(true);
    expect(loginLink.hidden).eq(false);
    expect(localStorage.getItem('Authorization')).eq(null);
  });

  [
    ['#id_token=mytoken', 'mytoken'],
    ['', 'Hunter1'],
  ].forEach(([input, expected]) => {
    it(`readCredentials works as expected (${input})`, async () => {
      localStorage.setItem('Authorization', 'Hunter1');

      readCredentials(input);

      expect(localStorage.getItem('Authorization')).eq(expected);
    });
  });

  it('parseApiResponse handles success', async () => {
    localStorage.setItem('Authorization', 'Hunter1');

    const result = await parseApiResponse(apiResponse);

    expect(result).eql(jsonResponse);
    expect(localStorage.getItem('Authorization')).eq('Hunter1');
  });

  it('parseApiResponse handles auth failure', async () => {
    localStorage.setItem('Authorization', 'Hunter1');
    const response = {
      ok: false,
      status: 400,
    };

    try {
      await parseApiResponse(response as Response);
    } catch {
      expect(localStorage.getItem('Authorization')).eq(null);
      return;
    }
    expect(false).eq(true);
  });

  it('parseApiResponse handles non-auth failure', async () => {
    localStorage.setItem('Authorization', 'Hunter1');
    const response = {
      ok: false,
      status: 500,
    };

    try {
      await parseApiResponse(response as Response);
    } catch {
      expect(localStorage.getItem('Authorization')).eq('Hunter1');
      return;
    }
    expect(false).eq(true);
  });

  it('parseJsonResponse handles no NextToken', async () => {
    const data: RowData[] = [];
    const search = new URLSearchParams({ MaxResults: '1000', NextToken: 'page-1' });

    parseJsonResponse(jsonResponse, data, mockAjaxParams, search);

    expect(ajaxSuccessStub.callCount).eq(1);
    expect(ajaxSuccessStub.firstCall.args[0]).eql(data);
    expect(ajaxSuccessStub.firstCall.args[0]).eql([
      {
        Name: 'Name',
        Id: 'i-1',
        Type: 'small',
        State: 'running',
        AZ: 'us-east-1',
        PublicIps: '192.168.0.1\n192.168.0.2',
        PrivateIps: '8.8.8.8',
      },
      {
        ...exampleInstance,
        PublicIps: '',
        PrivateIps: '',
      },
    ]);
  });

  it('parseJsonResponse handles NextToken', async () => {
    setLoggedInElementsVisibility(false);
    const data: RowData[] = [];
    const search = new URLSearchParams({
      MaxResults: '1000',
      NextToken: 'page-1',
    });
    const responseWithNextToken = {
      ...jsonResponse,
      NextToken: 'page-2',
    };

    parseJsonResponse(responseWithNextToken, data, mockAjaxParams, search);

    expect(ajaxSuccessStub.callCount).eq(0);
    expect(data).eql([
      {
        Name: 'Name',
        Id: 'i-1',
        Type: 'small',
        State: 'running',
        AZ: 'us-east-1',
        PublicIps: '192.168.0.1\n192.168.0.2',
        PrivateIps: '8.8.8.8',
      },
      exampleRow,
    ]);
    expect(search).eql(
      new URLSearchParams({
        MaxResults: '1000',
        NextToken: 'page-2',
      }),
    );
  });

  it('parseJsonResponse appends data', async () => {
    setLoggedInElementsVisibility(false);
    const data: RowData[] = [
      { ...exampleRow, Id: 'i-3' },
      { ...exampleRow, Id: 'i-4' },
    ];
    const search = new URLSearchParams({
      MaxResults: '1000',
      NextToken: 'page-1',
    });

    parseJsonResponse(jsonResponse, data, mockAjaxParams, search);

    expect(ajaxSuccessStub.callCount).eq(1);
    expect(ajaxSuccessStub.firstCall.args[0]).eql(data);
    expect(data).eql([
      { ...exampleRow, Id: 'i-3' },
      { ...exampleRow, Id: 'i-4' },
      {
        Name: 'Name',
        Id: 'i-1',
        Type: 'small',
        State: 'running',
        AZ: 'us-east-1',
        PublicIps: '192.168.0.1\n192.168.0.2',
        PrivateIps: '8.8.8.8',
      },
      exampleRow,
    ]);
    expect(search).eql(
      new URLSearchParams({
        MaxResults: '1000',
      }),
    );
  });

  it('fetchAllData handles no pagination', async () => {
    fetchStub.resolves(apiResponse);

    const ajaxParams = {
      success: (response: any) => {
        expect(response).eql([
          {
            Name: 'Name',
            Id: 'i-1',
            Type: 'small',
            State: 'running',
            AZ: 'us-east-1',
            PublicIps: '192.168.0.1\n192.168.0.2',
            PrivateIps: '8.8.8.8',
          },
          exampleRow,
        ]);
      },
    };

    await fetchAllData(ajaxParams);

    expect(fetchStub.callCount).eq(1);
  });

  it('fetchAllData handles pagination', async () => {
    fetchStub.onFirstCall().resolves({
      ...apiResponse,
      json: () => ({ ...jsonResponse, NextToken: 'page-2' }),
    });
    fetchStub.onSecondCall().resolves({
      ...apiResponse,
      json: () => ({
        Instances: [
          { ...exampleInstance, Id: 'i-3' },
          { ...exampleInstance, Id: 'i-4' },
        ],
        NextToken: 'page-3',
      }),
    });
    fetchStub.onThirdCall().resolves({
      ...apiResponse,
      json: () => ({
        Instances: [
          { ...exampleInstance, Id: 'i-5' },
          { ...exampleInstance, Id: 'i-6' },
        ],
      }),
    });

    const ajaxParams = {
      success: (response: any) => {
        expect(response).eql([
          {
            Name: 'Name',
            Id: 'i-1',
            Type: 'small',
            State: 'running',
            AZ: 'us-east-1',
            PublicIps: '192.168.0.1\n192.168.0.2',
            PrivateIps: '8.8.8.8',
          },
          exampleRow,
          { ...exampleRow, Id: 'i-3' },
          { ...exampleRow, Id: 'i-4' },
          { ...exampleRow, Id: 'i-5' },
          { ...exampleRow, Id: 'i-6' },
        ]);
      },
    };

    await fetchAllData(ajaxParams);
  });

  it('fetchAllData logsout on auth failure pagination', async () => {
    const loginStub = stub();
    localStorage.setItem('Authorization', 'Hunter1');
    document.getElementById('loginLink').onclick = loginStub;
    fetchStub.resolves({
      ok: false,
      status: 400,
    });

    const ajaxParams = {
      success: (_response: any) => {
        expect(false).eql(true);
      },
    };

    await fetchAllData(ajaxParams);

    expect(fetchStub.callCount).eq(1);
    expect(loginStub.callCount).eq(1);
    expect(localStorage.getItem('Authorization')).eq(null);
  });

  it('ajaxRequest behaves as expected', async () => {
    global.window.location.hash = 'id_token=Hunter1';
    fetchStub.resolves(apiResponse);

    ajaxRequest(mockAjaxParams);

    expect(global.window.location.hash).eq('');
    expect(localStorage.getItem('Authorization')).eq('Hunter1');
  });

  it('buttons returns expected buttons', async () => {
    const result = buttons();
    expect('btnLogOut' in result).eq(true);
  });

  it('login works', async () => {
    const loginStub = stub();
    document.getElementById('loginLink').onclick = loginStub;
    login()
    expect(loginStub.callCount).eq(1);
  });
});
